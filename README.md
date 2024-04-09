# WHIMC-Habitat-Assesser

Creates a socket server to send assessment requests to the API. Grades the student team's habitat using AI.

Refer to the [WHIMC-Habitat-Assesser Client README](/client/README.md) for client setup.


## Building

Compile a jar from the command line via Maven:
```
$ mvn install
```
It should show up in the target directory. Make sure to update your version number.

## Dependencies
- WHIMC Overworld Agent

## Commands

| Command                       | Description                               |
|-------------------------------|-------------------------------------------|
| `/habitats clients`           | lists currently active clients            |
| `/habitats disconnect`        | disconnects client with provided UUID     |
| `/habitats queue-list`        | lists assessment ids in the queue         |
| `/habitats queue-clear`       | clears the assessment queue               |
| `/habitats queue-remove <id>` | removes assessment with id from the queue |


## Config
### habitat_assessment
| Key    | Type     | Description        |
|--------|----------|--------------------|
| `host` | `string` | the websocket host |
| `port` | `string` | the websocket port |

### mysql
| Key        | Type     | Description         |
|------------|----------|---------------------|
| `host`     | `string` | the db sql host     |
| `port`     | `string` | the db sql port     |
| `database` | `string` | the db sql db name  |
| `username` | `string` | the db sql username |
| `password` | `string` | the db sql password |

### habitat_feedback
| Key                  | Type     | Description                                          |
|----------------------|----------|------------------------------------------------------|
| `<habitat category>` | `string` | feedback to give for the habitat assessment category |

**Example:**

```yaml
websocket:
  habitat_assessment:
    host: 0.0.0.0
    port: 8235
mysql:
  host: localhost
  port: 3306
  database: minecraft
  username: user
  password: pass
habitat_feedback:
  area: "providing shelter in a valley or underground to protect your base"
```
