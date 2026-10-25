# mustache-spec-conformance Specification

## Purpose

Define Chevron's reproducible relationship with the current upstream Mustache specification and require passing conformance for every module it vendors.

## Requirements

### Requirement: Current Mustache fixtures are vendored with provenance

Chevron SHALL vendor the complete upstream JSON fixture set from a recorded immutable Mustache specification revision. The vendor attribution SHALL name that revision and retain the upstream source and licence information.

#### Scenario: Fixture provenance is inspectable

- **WHEN** a developer inspects the vendored fixture attribution
- **THEN** it identifies the immutable upstream revision from which the fixtures were copied

#### Scenario: Current upstream modules are retained

- **WHEN** the current upstream JSON fixture set contains core and optional modules
- **THEN** the vendored fixture directory contains each of those JSON modules unchanged apart from Chevron's attribution file

### Requirement: Every vendored Mustache module passes conformance tests

Chevron SHALL execute every vendored current upstream JSON module as a passing conformance test. A fixture module SHALL not be omitted or marked unsupported because it exposes an implementation gap.

#### Scenario: Core fixture execution

- **WHEN** the conformance suite runs against the vendored core modules
- **THEN** every core case passes using the public render API

#### Scenario: Optional module execution

- **WHEN** the conformance suite runs a vendored optional module, including lambdas, dynamic names, or inheritance
- **THEN** every case passes through Chevron's public render API
