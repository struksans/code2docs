### E01-F01-S01 — <short title>

**Type:** Parity | Gap · **Labels:** <epic-slug>, <channel: ui | api | batch | integration> · **Status:** Draft

**Statement**
As a **<persona>**
I want **<capability>**
so that **<business value>**.

**Description**
<What the behaviour is, in business language. 2–6 sentences.>

**Business rules**
- BR-nn — <rule in plain language> *(source: product-spec BR-nn)*

**Acceptance criteria**

```gherkin
Feature: <feature name>

  Background:
    Given <common precondition>

  Scenario: <happy path>
    Given <state>
    When <action>
    Then <observable outcome>
    And <side effect: record stored / message published / notification sent>

  Scenario Outline: Reject invalid <field>
    Given <state>
    When <action> with <field> "<value>"
    Then the request is rejected with "<error>"

    Examples:
      | value | error |
      | ...   | ...   |

  Scenario: <not authorised>
    Given a user without <permission>
    When <action>
    Then access is denied
```

**Data & interface mapping**

| Legacy source | Kind | Field / path | Business meaning | Type / format | Req. | Validation / constraints | Dir. | Evidence |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

**Schemas**
- Request/response/message: see [api-spec › <operation>](../../api-spec.md#<anchor>)
- Entities: see [data-model › <Entity>](../../data-model.md#<anchor>)

```json
{ "$comment": "Deep specs only: compact JSON Schema of the payload", "type": "object", "required": [], "properties": {} }
```

Enumerations: `<FIELD>`: `A` = <meaning>, `B` = <meaning>

**Validation rules**

| Field | Rule | Legacy error code / message | Enforced in legacy at |
|---|---|---|---|
| | | | UI / API / service / DB constraint |

**Integrations touched**
- <business role of the system> — legacy: <protocol / endpoint / topic> (reference only)

**Dependencies**
Depends on: none

**Legacy evidence**
- `<path:line>` — <what it shows>

**Open questions**
- <question> *(owner: PO / architect / legacy SME)*

**Definition of Ready**
- [ ] Every field used in the AC is in the mapping table
- [ ] Validation rules and error messages confirmed
- [ ] Dependencies identified and exist in the backlog
- [ ] Open questions answered or accepted
- [ ] Testable without knowledge of the legacy implementation
