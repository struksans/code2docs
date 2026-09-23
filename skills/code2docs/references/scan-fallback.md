# Agent-only scan (no Python)

Use when Python is not available. Use your agent's search tool (Grep / ripgrep / `git grep` / `findstr` on Windows). Exclude: `node_modules`, `.git`, `dist`, `build`, `target`, `bin`, `obj`, `vendor`, `.venv`, `venv`, `__pycache__`, minified files, lock files.

Write results to `<output>/.code2docs/inventory.md` as one table per category:

```
## http_routes
| name | file:line | snippet |
```

Categories and patterns (regex, case-sensitive unless noted):

## entrypoints
- Python: `if __name__ == ["']__main__["']`, `uvicorn.run`, `app.run(`
- JS/TS: `"main":`, `"bin":`, `"start":` in package.json; `app.listen(`, `createServer(`
- Java/Kotlin: `public static void main`, `@SpringBootApplication`, `fun main(`
- C#: `static void Main`, `static async Task Main`, `WebApplication.CreateBuilder`, `Host.CreateDefaultBuilder`
- Go: `func main()`
- Containers: `^(CMD|ENTRYPOINT)` in Dockerfile, `command:` in compose

## http_routes
- Flask/FastAPI: `@\w+\.(route|get|post|put|patch|delete)\(`
- Django: `path\(|re_path\(` in `urls.py`
- Express/Koa/Fastify/Nest: `\b(app|router|server)\.(get|post|put|patch|delete|all|use)\(\s*['"\x60]/`, `@(Get|Post|Put|Patch|Delete|Controller)\(`
- Spring: `@(Get|Post|Put|Patch|Delete|Request)Mapping`
- ASP.NET: `\[(Http(Get|Post|Put|Patch|Delete)|Route)`, `Map(Get|Post|Put|Patch|Delete)\(`
- Go: `HandleFunc\(`, `\.(GET|POST|PUT|PATCH|DELETE)\(\s*"`
- GraphQL: `type Query`, `type Mutation`, `@(Query|Mutation|Resolver)\(`

## cli_args
`add_argument\(`, `@click\.(option|argument|command)`, `typer`, `\.option\(\s*['"]-`, `yargs`, `flag\.(String|Int|Bool)`, `cobra.Command`, `args\[`, `System.CommandLine`

## env_vars / config
`os\.environ`, `os\.getenv`, `process\.env\.`, `System\.getenv`, `@Value\("\$\{`, `Environment\.GetEnvironmentVariable`, `IConfiguration`, `os\.Getenv`, `viper\.`; also files `.env*`, `application*.yml|properties`, `appsettings*.json`, `config/*.yaml`

## file_io
`open\(`, `Path\(.*\)\.(read|write)_`, `fs\.(read|write|createReadStream|createWriteStream)`, `File(Reader|Writer|InputStream|OutputStream)`, `File\.(Read|Write)`, `os\.(Open|Create|ReadFile|WriteFile)`, `pd\.read_|to_csv\(|to_parquet\(`, `boto3.*s3`, `BlobClient`, `Storage\(`

## databases
Drivers/clients: `psycopg|asyncpg|pymysql|sqlite3|sqlalchemy|pymongo|redis|elasticsearch|cassandra`, `pg|mysql2|mongoose|mongodb|ioredis|knex|prisma|typeorm|sequelize`, `jdbc:|JdbcTemplate|EntityManager|JpaRepository`, `DbContext|SqlConnection|NpgsqlConnection`, `database/sql|gorm`, raw SQL `\b(SELECT|INSERT INTO|UPDATE|DELETE FROM)\b` (case-insensitive)

## orm_models
`class \w+\((db\.)?Model\)`, `Base = declarative_base`, `__tablename__`, `@Entity`, `@Table\(`, `DbSet<`, `model \w+ \{` (Prisma), `@Entity\(\)` (TypeORM), `mongoose\.Schema`, `CREATE TABLE` in migrations

## messaging
`KafkaProducer|KafkaConsumer|@KafkaListener|kafkajs|confluent_kafka|sarama`, `pika|amqplib|RabbitTemplate|@RabbitListener`, `sqs|sns|SQSClient|SNSClient`, `ServiceBusClient|EventHubProducerClient`, `PubSub|pubsub_v1`, `nats|redis.*(publish|subscribe)`, `celery|@shared_task|bull|BullMQ`

## http_clients (outbound)
`requests\.(get|post|put|delete)|httpx|aiohttp`, `axios|fetch\(|got\(`, `RestTemplate|WebClient|FeignClient|OkHttp`, `HttpClient`, `http\.(Get|Post|NewRequest)`

## schedulers
`@Scheduled|cron|schedule\.every|APScheduler|setInterval|node-cron|Quartz|BackgroundService|IHostedService|CronJob`

## ui_routes
React Router `<Route|createBrowserRouter`, Next.js `pages/` `app/**/page.tsx`, Angular `Routes = \[`, Vue `createRouter`

## contracts
Files: `*openapi*.y?ml|*swagger*.json|*.proto|*.graphql|*.gql|*asyncapi*|*.avsc|*.schema.json|migrations/**|*.sql`

After grepping, open the top hits per category to confirm; discard matches in tests, examples and comments unless the user asked to include tests.
