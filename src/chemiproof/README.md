# `chemiproof` package

Implemented in M0: `errors` (status codes), `config` (validated YAML configs), `provenance` (config hash, run ID, environment info), `logging_utils`, `data/schema` (EEM record contract), `data/synthetic` (synthetic test fixtures only), `pipeline` (stages that fail honestly), `cli`.

Everything else (parser, preprocessing, models, evaluation, UI) is planned for M1+ per `docs/engineering/04_ARCHITECTURE.md`. No stage produces predictions or metrics today.
