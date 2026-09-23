#!/usr/bin/env python3
"""Inventory a code repository for code2docs.

Finds entry points, HTTP routes, CLI arguments, environment/config access,
file I/O, databases, ORM models, messaging, outbound HTTP clients,
schedulers, UI routes and contract files (OpenAPI, proto, SQL, ...).

Standard library only (Python 3.8+). Output is JSON; the agent reads it
and then opens the referenced files to confirm and deepen the findings.

Usage:
    python3 scan_repo.py <repo> [--out inventory.json]
                         [--include GLOB ...] [--exclude GLOB ...]
                         [--include-tests] [--max-per-category N]
"""

import argparse
import fnmatch
import json
import os
import re
import sys
from collections import Counter, defaultdict

LANGUAGES = {
    ".py": "python",
    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript",
    ".java": "java", ".kt": "kotlin", ".kts": "kotlin", ".scala": "scala",
    ".cs": "csharp", ".fs": "fsharp", ".vb": "vbnet",
    ".go": "go", ".rs": "rust", ".rb": "ruby", ".php": "php",
    ".swift": "swift", ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp", ".cc": "cpp",
    ".sql": "sql", ".sh": "shell", ".ps1": "powershell",
    ".vue": "vue", ".svelte": "svelte",
    ".yaml": "yaml", ".yml": "yaml", ".json": "json", ".xml": "xml",
    ".proto": "protobuf", ".graphql": "graphql", ".gql": "graphql",
}

MANIFESTS = {
    "package.json": "node", "pyproject.toml": "python", "setup.py": "python",
    "setup.cfg": "python", "requirements.txt": "python", "Pipfile": "python",
    "pom.xml": "maven", "build.gradle": "gradle", "build.gradle.kts": "gradle",
    "go.mod": "go", "Cargo.toml": "rust", "composer.json": "php", "Gemfile": "ruby",
    "Dockerfile": "docker", "docker-compose.yml": "compose", "docker-compose.yaml": "compose",
    "compose.yml": "compose", "compose.yaml": "compose", "Chart.yaml": "helm",
    "serverless.yml": "serverless", "template.yaml": "sam", "host.json": "azure-functions",
}
MANIFEST_SUFFIXES = {".csproj": "dotnet", ".sln": "dotnet", ".fsproj": "dotnet", ".tf": "terraform"}

DEFAULT_EXCLUDES = [
    ".git", "node_modules", "dist", "build", "target", "bin", "obj", "out",
    "vendor", ".venv", "venv", "env", "__pycache__", ".tox", ".mypy_cache",
    ".pytest_cache", ".next", ".nuxt", "coverage", ".idea", ".vscode",
    ".gradle", ".terraform", "site-packages", ".code2docs",
]
TEST_HINTS = re.compile(r"(^|/)(tests?|__tests__|spec|specs|testdata|fixtures|e2e)(/|$)|[._-](test|spec)\.[a-z]+$|_test\.go$|^test_", re.I)
SKIP_FILE = re.compile(r"\.(min\.js|map|lock|png|jpe?g|gif|svg|ico|pdf|zip|gz|jar|dll|exe|so|dylib|woff2?|ttf|eot|mp[34]|bin)$|(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|go\.sum|Cargo\.lock)$", re.I)
MAX_FILE_BYTES = 1_000_000

# Contract / schema files recognised by name.
CONTRACT_FILES = [
    ("openapi", re.compile(r"(openapi|swagger)[^/]*\.(ya?ml|json)$", re.I)),
    ("asyncapi", re.compile(r"asyncapi[^/]*\.(ya?ml|json)$", re.I)),
    ("protobuf", re.compile(r"\.proto$", re.I)),
    ("graphql", re.compile(r"\.(graphql|gql)$", re.I)),
    ("avro", re.compile(r"\.avsc$", re.I)),
    ("json-schema", re.compile(r"\.schema\.json$", re.I)),
    ("sql-migration", re.compile(r"(migrations?|db/migrate|flyway|liquibase|alembic/versions)/.*\.(sql|py|xml|ya?ml|rb|js|ts)$", re.I)),
    ("sql", re.compile(r"\.sql$", re.I)),
    ("env-example", re.compile(r"(^|/)\.env(\.[\w-]+)?$|\.env\.example$", re.I)),
    ("app-config", re.compile(r"(^|/)(application[\w-]*\.(ya?ml|properties)|appsettings[\w.-]*\.json|config/[\w.-]+\.(ya?ml|json|toml))$", re.I)),
    ("k8s/helm", re.compile(r"(^|/)(k8s|kubernetes|helm|charts|deploy|manifests)/.*\.ya?ml$", re.I)),
]

# (category, kind, regex, name-group-builder). Regexes run per line.
R = re.compile
HTTP_VERB = r"(get|post|put|patch|delete|head|options|all)"
PATTERNS = [
    # ---- entry points
    ("entrypoints", "python-main", R(r"if\s+__name__\s*==\s*['\"]__main__['\"]"), None),
    ("entrypoints", "python-server", R(r"\b(uvicorn\.run|app\.run|serve\(|gunicorn)\b"), None),
    ("entrypoints", "node-listen", R(r"\b\w+\.listen\(\s*[\w.]+"), None),
    ("entrypoints", "java-main", R(r"public\s+static\s+void\s+main\s*\("), None),
    ("entrypoints", "spring-boot", R(r"@SpringBootApplication"), None),
    ("entrypoints", "kotlin-main", R(r"^\s*fun\s+main\s*\("), None),
    ("entrypoints", "dotnet-main", R(r"static\s+(async\s+)?(void|Task|int|Task<int>)\s+Main\s*\("), None),
    ("entrypoints", "dotnet-host", R(r"\b(WebApplication\.CreateBuilder|Host\.CreateDefaultBuilder|FunctionsApplication)"), None),
    ("entrypoints", "go-main", R(r"^func\s+main\s*\(\s*\)"), None),
    ("entrypoints", "rust-main", R(r"^\s*(async\s+)?fn\s+main\s*\("), None),
    ("entrypoints", "docker", R(r"^\s*(CMD|ENTRYPOINT)\s+(.+)"), 2),
    ("entrypoints", "lambda/function", R(r"\b(def\s+(lambda_)?handler\s*\(|exports\.handler\s*=|@FunctionName\(|@app\.function_name|func\.HttpTrigger|\[Function\()"), None),

    # ---- HTTP routes (name = "VERB path")
    ("http_routes", "flask/fastapi", R(r"@\w+\.(route|" + HTTP_VERB + r"|websocket)\(\s*['\"]([^'\"]*)['\"]", re.I), "verb:1,path:3"),
    ("http_routes", "django", R(r"\b(re_)?path\(\s*r?['\"]([^'\"]*)['\"]"), "path:2"),
    ("http_routes", "express-like", R(r"(?<!@)\b(app|router|server|api|routes?)\.(" + HTTP_VERB[1:-1] + r"|use|route)\(\s*['\"`]([^'\"`]*)['\"`]", re.I), "verb:2,path:3"),
    ("http_routes", "nest/decorator", R(r"@(Get|Post|Put|Patch|Delete|All|Controller)\(\s*['\"]?([^'\")]*)['\"]?\s*\)"), "verb:1,path:2"),
    ("http_routes", "spring", R(r"@(Get|Post|Put|Patch|Delete|Request)Mapping\s*(\(\s*(value\s*=\s*|path\s*=\s*)?\{?\s*\"([^\"]*)\")?"), "verb:1,path:4"),
    ("http_routes", "aspnet-attr", R(r"\[(Http(Get|Post|Put|Patch|Delete)|Route)(\(\s*\"([^\"]*)\")?"), "verb:2,path:4"),
    ("http_routes", "aspnet-minimal", R(r"\.Map(Get|Post|Put|Patch|Delete|Methods)?\(\s*\"([^\"]*)\""), "verb:1,path:2"),
    ("http_routes", "go-http", R(r"\b(HandleFunc|Handle)\(\s*\"([^\"]*)\""), "path:2"),
    ("http_routes", "go-router", R(r"\.(GET|POST|PUT|PATCH|DELETE)\(\s*\"([^\"]*)\""), "verb:1,path:2"),
    ("http_routes", "jaxrs", R(r"@Path\(\s*\"([^\"]*)\"\)"), "path:1"),
    ("http_routes", "graphql", R(r"\b(type\s+(Query|Mutation|Subscription)\b|@(Query|Mutation|Resolver|Subscription)\()"), None),
    ("http_routes", "grpc-service", R(r"^\s*service\s+(\w+)\s*\{"), 1),
    ("http_routes", "websocket", R(r"\b(WebSocketServer|socket\.io|@WebSocketGateway|SignalR|MapHub<|websockets\.serve)"), None),

    # ---- CLI
    ("cli_args", "argparse", R(r"\.add_argument\(\s*['\"]([^'\"]+)['\"]"), 1),
    ("cli_args", "click/typer", R(r"@(click|app)\.(option|argument|command)\(\s*['\"]?([^'\",)]*)"), 3),
    ("cli_args", "commander/yargs", R(r"\.(option|requiredOption|command|positional)\(\s*['\"`]([^'\"`]+)"), 2),
    ("cli_args", "go-flag", R(r"\bflag\.(String|Int|Bool|Duration|Float64)(Var)?\([^\"]*\"([^\"]+)\""), 3),
    ("cli_args", "cobra", R(r"&cobra\.Command\{|Use:\s*\"([^\"]+)\""), 1),
    ("cli_args", "clap", R(r"#\[(arg|command)\(|Arg::new\(\s*\"([^\"]+)\""), 2),
    ("cli_args", "sys.argv", R(r"\b(sys\.argv|process\.argv|os\.Args|args\[\d+\])"), None),

    # ---- env / config
    ("env_vars", "python", R(r"os\.(environ(?:\.get)?\s*[\[(]\s*|getenv\(\s*)['\"]([A-Z0-9_]+)['\"]"), 2),
    ("env_vars", "node", R(r"process\.env\.([A-Z0-9_]+)|process\.env\[\s*['\"]([A-Z0-9_]+)['\"]"), "first"),
    ("env_vars", "java", R(r"System\.getenv\(\s*\"([A-Z0-9_]+)\""), 1),
    ("env_vars", "spring-value", R(r"@Value\(\s*\"\$\{([^}:]+)"), 1),
    ("env_vars", "dotnet", R(r"(GetEnvironmentVariable\(\s*\"([^\"]+)\"|Configuration\[\s*\"([^\"]+)\"\]|GetSection\(\s*\"([^\"]+)\"|GetValue<[^>]+>\(\s*\"([^\"]+)\")"), "first"),
    ("env_vars", "go", R(r"os\.(Getenv|LookupEnv)\(\s*\"([^\"]+)\""), 2),
    ("env_vars", "rust", R(r"env::var\(\s*\"([^\"]+)\""), 1),
    ("env_vars", "settings-lib", R(r"\b(BaseSettings|pydantic_settings|dotenv|viper\.(Get\w*)\(\s*\"([^\"]+)\")"), 3),
    ("env_vars", "docker/compose", R(r"^\s*(ENV|ARG)\s+([A-Z0-9_]+)"), 2),

    # ---- file I/O
    ("file_io", "python-open", R(r"\bopen\(\s*([^,)]+)(,\s*['\"]([rwab+xt]+)['\"])?"), 1),
    ("file_io", "python-path", R(r"\.(read_text|write_text|read_bytes|write_bytes)\("), None),
    ("file_io", "pandas", R(r"\b(pd|pandas)\.read_(csv|excel|json|parquet|sql|table)\(|\.to_(csv|excel|json|parquet|sql)\("), None),
    ("file_io", "node-fs", R(r"\bfs(\.promises)?\.(readFile|writeFile|appendFile|createReadStream|createWriteStream|readdir)(Sync)?\("), None),
    ("file_io", "java", R(r"\b(FileReader|FileWriter|FileInputStream|FileOutputStream|Files\.(read|write|lines|newBuffered)\w*)\b"), None),
    ("file_io", "dotnet", R(r"\bFile\.(Read|Write|Append|Open)\w*\(|\bStream(Reader|Writer)\("), None),
    ("file_io", "go", R(r"\b(os\.(Open|Create|ReadFile|WriteFile|OpenFile)|ioutil\.(ReadFile|WriteFile))\("), None),
    ("file_io", "object-storage", R(r"\b(s3|S3Client|boto3\.(client|resource)\(\s*['\"]s3|BlobServiceClient|BlobClient|ContainerClient|storage\.Client|GetObject|PutObject|upload_file|download_file)\b"), None),
    ("file_io", "upload", R(r"\b(UploadFile|multer|IFormFile|MultipartFile|request\.files)\b"), None),

    # ---- databases
    ("databases", "postgres", R(r"\b(psycopg2?|asyncpg|pg\.Pool|new\s+Pool\(|Npgsql\w*|jdbc:postgresql|postgres(ql)?://|lib/pq|pgx)\b", re.I), None),
    ("databases", "mysql", R(r"\b(pymysql|mysqlclient|mysql2?|MySqlConnection|jdbc:mysql|mysql://|go-sql-driver/mysql)\b", re.I), None),
    ("databases", "sqlserver", R(r"\b(pyodbc|SqlConnection|jdbc:sqlserver|mssql|tedious)\b"), None),
    ("databases", "oracle", R(r"\b(cx_Oracle|oracledb|jdbc:oracle|OracleConnection)\b"), None),
    ("databases", "sqlite", R(r"\b(sqlite3|better-sqlite3|SqliteConnection|sqlite://)\b", re.I), None),
    ("databases", "mongodb", R(r"\b(pymongo|MongoClient|mongoose|mongodb(\+srv)?://|MongoRepository)\b"), None),
    ("databases", "redis", R(r"\b(redis\.Redis|ioredis|createClient\(|StackExchange\.Redis|Jedis|Lettuce|go-redis|redis://)\b"), None),
    ("databases", "elasticsearch", R(r"\b(Elasticsearch\(|@elastic/elasticsearch|OpenSearch|NEST|ElasticClient)\b"), None),
    ("databases", "dynamodb/cosmos", R(r"\b(dynamodb|DynamoDB\w*|CosmosClient|azure\.cosmos|Firestore|firestore)\b"), None),
    ("databases", "cassandra", R(r"\b(cassandra\.cluster|cassandra-driver|CqlSession)\b"), None),
    ("databases", "orm/client", R(r"\b(create_engine|sessionmaker|SQLAlchemy\(|PrismaClient|DataSource\(|TypeOrmModule|Sequelize\(|knex\(|JdbcTemplate|EntityManager|DbContext\b|gorm\.Open|sql\.Open|Diesel|sqlx::)"), None),
    ("databases", "raw-sql", R(r"['\"`]\s*(SELECT\s+.+\s+FROM\s+([\w.\"`\[\]]+)|INSERT\s+INTO\s+([\w.\"`\[\]]+)|UPDATE\s+([\w.\"`\[\]]+)\s+SET|DELETE\s+FROM\s+([\w.\"`\[\]]+))", re.I), "first:2"),

    # ---- ORM models / entities
    ("orm_models", "sqlalchemy/django", R(r"^\s*class\s+(\w+)\s*\(([\w.]*(Model|Base|DeclarativeBase|SQLModel|Document|models\.Model))[^)]*\)"), 1),
    ("orm_models", "tablename", R(r"__tablename__\s*=\s*['\"](\w+)['\"]"), 1),
    ("orm_models", "jpa", R(r"@(Entity|Table\(\s*name\s*=\s*\"(\w+)\")"), 2),
    ("orm_models", "efcore", R(r"\bDbSet<(\w+)>\s+(\w+)"), 1),
    ("orm_models", "typeorm", R(r"@Entity\(\s*['\"]?(\w*)"), 1),
    ("orm_models", "mongoose", R(r"new\s+(mongoose\.)?Schema\(|mongoose\.model\(\s*['\"](\w+)['\"]"), 2),
    ("orm_models", "prisma", R(r"^\s*model\s+(\w+)\s*\{"), 1),
    ("orm_models", "gorm", R(r"gorm\.Model"), None),
    ("orm_models", "sql-ddl", R(r"CREATE\s+TABLE\s+(IF\s+NOT\s+EXISTS\s+)?([\w.\"`\[\]]+)", re.I), 2),
    ("orm_models", "pydantic/dataclass", R(r"^\s*class\s+(\w+)\s*\(\s*(BaseModel|Schema|TypedDict)\s*\)"), 1),

    # ---- messaging
    ("messaging", "kafka", R(r"\b(KafkaProducer|KafkaConsumer|@KafkaListener|KafkaTemplate|kafkajs|confluent_kafka|aiokafka|sarama|ProducerBuilder|ConsumerBuilder)\b|topics?\s*[=:]\s*['\"]([\w.\-]+)['\"]"), 2),
    ("messaging", "topic-literal", R(r"\b(producer|kafka\w*|template|publisher|sender|client|channel)\.(send|produce|publish|send_message|basic_publish)\(\s*(topic\s*=\s*)?['\"]([\w.\-/]+)['\"]", re.I), 4),
    ("messaging", "rabbitmq", R(r"\b(pika|amqplib|amqp://|RabbitTemplate|@RabbitListener|RabbitMQ|basic_publish|basic_consume|queue_declare|exchange_declare|MassTransit)\b"), None),
    ("messaging", "aws", R(r"\b(sqs|sns|SQSClient|SNSClient|SendMessageCommand|PublishCommand|kinesis|EventBridge\w*)\b", re.I), None),
    ("messaging", "azure", R(r"\b(ServiceBusClient|ServiceBusSender|ServiceBusProcessor|EventHubProducerClient|EventHubConsumerClient|QueueClient|ServiceBusTrigger|EventGrid\w*)\b"), None),
    ("messaging", "gcp", R(r"\b(pubsub_v1|PubSub\(|@google-cloud/pubsub|PublisherClient|SubscriberClient)\b"), None),
    ("messaging", "nats/redis-pubsub", R(r"\b(nats\.connect|NATS|\.publish\(|\.subscribe\()\b"), None),
    ("messaging", "task-queue", R(r"\b(Celery\(|@shared_task|@\w+\.task\b|BullMQ|new\s+Queue\(|Sidekiq|Hangfire|rq\.Queue)\b"), None),
    ("messaging", "email/sms/push", R(r"\b(smtplib|nodemailer|SendGrid|sendgrid|JavaMailSender|SmtpClient|twilio|Twilio|firebase_admin\.messaging|SES|sesv2)\b"), None),

    # ---- outbound HTTP
    ("http_clients", "python", R(r"\b(requests|httpx|session)\.(get|post|put|patch|delete|request)\(\s*(f?['\"]([^'\"]+)['\"])?"), 4),
    ("http_clients", "python-async", R(r"\baiohttp\.ClientSession|httpx\.(Async)?Client\("), None),
    ("http_clients", "node", R(r"\b(axios(\.(get|post|put|patch|delete|create))?|fetch|got|superagent)\(\s*(['\"`]([^'\"`]+)['\"`])?"), 5),
    ("http_clients", "java", R(r"\b(RestTemplate|WebClient|@FeignClient|OkHttpClient|HttpClient\.new|RestClient)\b(\(\s*(name|url)\s*=\s*\"([^\"]+)\")?"), 4),
    ("http_clients", "dotnet", R(r"\b(HttpClient|IHttpClientFactory|RestSharp|Refit)\b"), None),
    ("http_clients", "go", R(r"\bhttp\.(Get|Post|NewRequest(WithContext)?)\(\s*(\"([^\"]+)\")?"), 4),
    ("http_clients", "url-literal", R(r"['\"`](https?://[^'\"`\s{}$]+)['\"`]"), 1),

    # ---- schedulers
    ("schedulers", "cron-like", R(r"(@Scheduled\(|\bcron\s*[=:(]|schedule\.every|APScheduler|BackgroundScheduler|node-cron|cron\.schedule\(|setInterval\(|Quartz|IHostedService|BackgroundService|TimerTrigger|@periodic_task|beat_schedule|CronJob)"), None),

    # ---- UI routes
    ("ui_routes", "react-router", R(r"<Route\s+[^>]*path=['\"{]+([^'\"}]+)|createBrowserRouter\("), 1),
    ("ui_routes", "angular/vue", R(r"\{\s*path:\s*['\"]([^'\"]*)['\"]\s*,\s*(component|loadChildren|loadComponent|redirectTo)"), 1),
]

FLASK_METHODS = re.compile(r"methods\s*=\s*[\[(]([^\])]*)[\])]")
SENSITIVE = re.compile(r"(password|passwd|secret|token|api[_-]?key|private[_-]?key|credential)\s*[=:]\s*['\"][^'\"]{4,}['\"]", re.I)


def build_name(match, spec):
    """Turn a regex match into a short display name according to spec."""
    if spec is None:
        return match.group(0).strip()[:80]
    if isinstance(spec, int):
        val = match.group(spec) if spec <= (match.re.groups or 0) else None
        return (val or match.group(0)).strip()[:120]
    if spec.startswith("first"):
        start = int(spec.split(":")[1]) if ":" in spec else 1
        for i in range(start, (match.re.groups or 0) + 1):
            if match.group(i):
                return match.group(i).strip()[:120]
        return match.group(0).strip()[:80]
    parts = dict(p.split(":") for p in spec.split(","))
    verb = match.group(int(parts["verb"])) if "verb" in parts else None
    path = match.group(int(parts["path"])) if "path" in parts else None
    verb = (verb or "").upper()
    if verb in ("ROUTE", "REQUEST", "USE", "MAPPING", "METHODS", "CONTROLLER", "ALL", "HTTP"):
        verb = verb if verb in ("USE", "CONTROLLER") else "ANY"
    name = " ".join(x for x in (verb, path if path is not None else "") if x)
    return name or match.group(0).strip()[:80]


def excluded(rel, excludes, include, include_tests):
    parts = rel.split("/")
    if any(p in DEFAULT_EXCLUDES for p in parts[:-1]):
        return True
    if any(fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(parts[-1], g) for g in excludes):
        return True
    if include and not any(fnmatch.fnmatch(rel, g) for g in include):
        return True
    if not include_tests and TEST_HINTS.search(rel):
        return True
    return False


def scan(root, include, excludes, include_tests, max_per_category):
    root = os.path.abspath(root)
    languages = Counter()
    manifests = []
    contracts = []
    findings = defaultdict(list)
    counts = Counter()
    seen = set()
    secrets_seen = 0
    files_scanned = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in DEFAULT_EXCLUDES and not d.startswith(".") or d in (".github",))
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            if SKIP_FILE.search(rel) or excluded(rel, excludes, include, include_tests):
                continue
            ext = os.path.splitext(fn)[1].lower()
            if fn in MANIFESTS or fn.startswith("Dockerfile"):
                manifests.append({"file": rel, "kind": MANIFESTS.get(fn, "docker")})
            elif ext in MANIFEST_SUFFIXES:
                manifests.append({"file": rel, "kind": MANIFEST_SUFFIXES[ext]})
            for kind, rx in CONTRACT_FILES:
                if rx.search(rel):
                    contracts.append({"kind": kind, "name": fn, "file": rel, "line": 1, "snippet": ""})
                    break
            lang = LANGUAGES.get(ext)
            is_docker = fn.startswith("Dockerfile")
            if not lang and not is_docker:
                continue
            try:
                if os.path.getsize(full) > MAX_FILE_BYTES:
                    continue
                with open(full, "r", encoding="utf-8", errors="replace") as fh:
                    lines = fh.readlines()
            except OSError:
                continue
            files_scanned += 1
            if lang:
                languages[lang] += 1
            line_hits = set()
            data_file = lang in ("yaml", "json", "xml")
            for lineno, line in enumerate(lines, 1):
                if len(line) > 500:
                    line = line[:500]
                stripped = line.strip()
                if not stripped or stripped.startswith(("#!", "# ", "//", "* ", "/*")):
                    continue
                if SENSITIVE.search(line):
                    secrets_seen += 1
                    continue
                for category, kind, rx, spec in PATTERNS:
                    if data_file and category not in ("http_clients",):
                        continue
                    if kind == "docker" and not is_docker:
                        continue
                    if is_docker and kind not in ("docker", "docker/compose"):
                        continue
                    if kind == "url-literal" and ("http_clients", lineno) in line_hits:
                        continue
                    for m in rx.finditer(line):
                        name = build_name(m, spec)
                        if kind == "flask/fastapi" and name.startswith("ANY "):
                            methods = FLASK_METHODS.search(line)
                            if methods:
                                name = "%s %s" % ("|".join(re.findall(r"\w+", methods.group(1))).upper(), name[4:])
                        key = (category, rel, lineno, name)
                        if key in seen:
                            continue
                        seen.add(key)
                        line_hits.add((category, lineno))
                        counts[category] += 1
                        if len(findings[category]) < max_per_category:
                            findings[category].append({
                                "kind": kind, "name": name, "file": rel,
                                "line": lineno, "snippet": stripped[:200],
                            })

    findings["contracts"] = contracts[:max_per_category]
    counts["contracts"] = len(contracts)
    truncated = {c: n for c, n in counts.items() if n > max_per_category}
    return {
        "root": root,
        "summary": {
            "files_scanned": files_scanned,
            "languages": dict(languages.most_common()),
            "counts": dict(counts),
            "truncated_categories": truncated,
            "lines_skipped_as_possible_secrets": secrets_seen,
        },
        "manifests": manifests,
        "findings": {c: findings.get(c, []) for c in (
            "entrypoints", "http_routes", "cli_args", "env_vars", "file_io",
            "databases", "orm_models", "messaging", "http_clients",
            "schedulers", "ui_routes", "contracts")},
        "notes": [
            "Heuristic regex scan: confirm every finding by opening the file.",
            "Test folders are excluded unless --include-tests is given.",
            "Lines that look like hard-coded secrets are skipped and never copied.",
        ],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Inventory a code repository for code2docs.")
    ap.add_argument("repo", help="path to the repository or sub-folder to scan")
    ap.add_argument("--out", help="write JSON here (default: stdout)")
    ap.add_argument("--include", action="append", default=[], help="glob of paths to include (repeatable)")
    ap.add_argument("--exclude", action="append", default=[], help="glob of paths to exclude (repeatable)")
    ap.add_argument("--include-tests", action="store_true", help="also scan test folders/files")
    ap.add_argument("--max-per-category", type=int, default=500, help="cap findings per category (default 500)")
    args = ap.parse_args(argv)

    if not os.path.isdir(args.repo):
        ap.error("not a directory: %s" % args.repo)
    result = scan(args.repo, args.include, args.exclude, args.include_tests, args.max_per_category)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        s = result["summary"]
        print("Scanned %d files -> %s" % (s["files_scanned"], args.out))
        for cat, n in sorted(s["counts"].items()):
            print("  %-13s %d" % (cat, n))
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
