# Distribution Registry

Operational record for distributing the official Openapi.com MCP server and
SDK across public and private MCP directories, aggregators, registries, and
operator-focused catalogs.

This file is intentionally written in English because it is also the source of
truth for external submissions. Keep the status and last-checked date current;
do not mark an entry as published until the external listing or merged pull
request can be linked.

## Product being distributed

| Field | Value |
| --- | --- |
| Product | `openapi-mcp-sdk` — official Openapi.com MCP server and Python SDK |
| Repository | [openapi/mcp-server](https://github.com/openapi/mcp-server) |
| Package | [openapi-mcp-sdk on PyPI](https://pypi.org/project/openapi-mcp-sdk/) |
| Homepage | [openapi.com](https://openapi.com/) |
| Install | `uvx openapi-mcp-sdk server` |
| Other runtimes | `pipx run openapi-mcp-sdk server`, `pip install openapi-mcp-sdk` |
| Deployment | Docker / Docker Compose; HTTP/SSE server on port `8080` by default |
| Authentication | Bearer token forwarding through the client request |
| License | MIT |
| Positioning | Secure, ready-to-run API gateway plus reusable Python MCP SDK |

### Canonical short description

> Official Openapi.com MCP server and Python SDK: a ready-to-run, authenticated
> MCP gateway for Openapi.com APIs, installable with `uvx openapi-mcp-sdk
> server` or deployable with Docker.

Use the repository, PyPI, and homepage links above as the canonical links. Do
not create tracking redirects or duplicate project pages. External referrals
should land on GitHub so that stars, issues, forks, and documentation traffic
are attributable to the source repository.

## Submission tracker

Status values: `Planned` → `Draft ready` → `Submitted` → `Published` →
`Needs update` / `Rejected`.

| Aggregator / registry | Nature | Listing target | Status | External record | Last checked |
| --- | --- | --- | --- | --- | --- |
| [awesome-mcp](https://github.com/eon01/awesome-mcp) | Public, community-curated GitHub list | Server Frameworks and SDKs / Open Source | Draft ready | _Add PR or issue URL after submission_ | 2026-08-07 |
| [awesome-agentic-devops](https://github.com/DevOpsAIguru123/awesome-agentic-devops) | Public, scored DevOps/MCP catalog | MCP server / API and platform tooling category selected by maintainer | Draft ready | _Add PR URL after submission_ | 2026-08-07 |
| [Official MCP Registry](https://registry.modelcontextprotocol.io/) | Official, machine-readable registry | `io.github.openapi/mcp-server` namespace | Planned | _Requires `.mcp/server.json` and publisher authentication_ | 2026-08-07 |
| [Docker MCP Registry](https://github.com/docker/mcp-registry) | Official container catalog | Docker-built or community-built MCP server | Planned | _Requires container image and registry PR_ | 2026-08-07 |
| [Glama](https://glama.ai/) | Public directory, inspector, gateway | GitHub repository indexing | Planned | _Submit GitHub repository_ | 2026-08-07 |
| [Smithery](https://smithery.ai/) | Public registry and hosted distribution | Remote HTTPS server or MCPB bundle | Planned | _Requires public Streamable HTTP/OAuth or MCPB_ | 2026-08-07 |
| [PulseMCP](https://www.pulsemcp.com/servers) | Public directory and enriched sub-registry | Manual submission / official registry sync | Planned | _Submit via `/submit`_ | 2026-08-07 |
| [mcp.so](https://mcp.so/) | Public community directory | GitHub/Docker listing | Planned | _Confirm current submission route_ | 2026-08-07 |
| [MCPFind](https://mcpfind.org/) | Public directory and client setup guides | GitHub repository / install metadata | Planned | _Confirm listing workflow_ | 2026-08-07 |
| [mcpservers.org](https://mcpservers.org/) | Public MCP server directory | Server page and installation metadata | Planned | _Confirm listing workflow_ | 2026-08-07 |
| [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) | Public curated GitHub list | API integrations / business tools | Planned | _Open PR after checking contribution rules_ | 2026-08-07 |
| [GitHub MCP topics](https://github.com/topics/awesome-mcp-servers) | Public GitHub discovery surface | Repository topics and metadata | Planned | _Update repository topics and description_ | 2026-08-07 |
| [Docker Hub](https://hub.docker.com/) | Public container distribution | `openapi/openapi-mcp-server` image | Planned | _Requires image namespace and release workflow_ | 2026-08-07 |
| [GitHub Container Registry](https://ghcr.io/) | Public OCI distribution | `ghcr.io/openapi/mcp-server` image | Planned | _Requires OCI publishing workflow_ | 2026-08-07 |
| [Private Docker MCP catalog](https://docs.docker.com/ai/mcp-catalog-and-toolkit/cli/) | Private enterprise catalog | OCI catalog for internal clients | Planned | _Requires organization OCI registry_ | 2026-08-07 |
| [Internal MCP Registry](https://github.com/modelcontextprotocol/registry) | Private fork / approved catalog | Organization namespace and allowlist | Planned | _Requires an internal owner and policy_ | 2026-08-07 |

## Multi-round distribution plan

Run the rounds in order. A round is complete only when the listing is live,
the external URL is recorded above, and the listing can be tested from a clean
client. Do not submit the same artifact repeatedly when a downstream directory
already imports it from the Official MCP Registry.

### Round 0 — Distribution foundations

Goal: make the project machine-readable and reproducible before directory
submissions.

- Add and validate `.mcp/server.json` for the Official MCP Registry.
- Confirm the public transport and authentication contract. The current
  repository documents HTTP/SSE and bearer-token forwarding; Smithery expects a
  public Streamable HTTP endpoint and OAuth support when authentication is
  required.
- Build a versioned Docker image, publish it to Docker Hub and GHCR, and add a
  multi-architecture release workflow if supported by the hosting policy.
- Add repository topics such as `mcp`, `mcp-server`, `model-context-protocol`,
  `openapi`, `api-gateway`, `python`, and `fastmcp`.
- Prepare a public demo endpoint or a safe metadata-only scan path. Never use
  production bearer tokens in directory scanners.

Exit criteria: `server.json`, container image, README installation commands,
and a scanner-safe authentication story are all consistent.

### Round 1 — Official and high-reach discovery

Submit to the Official MCP Registry, Docker MCP Registry, Glama, Smithery, and
PulseMCP. These channels maximize machine discoverability, client integration,
container distribution, and directory traffic. Capture the resulting server
IDs, listing URLs, package digests, and review notes in the tracker.

### Round 2 — Community and editorial discovery

Submit to `awesome-mcp`, `awesome-agentic-devops`, `awesome-mcp-servers`,
mcp.so, MCPFind, and mcpservers.org. Adapt the description to each audience:
SDK/gateway for developer lists, authenticated API automation for DevOps lists,
and concrete installation commands for server directories.

Every PR or issue should contain one canonical project link, one short factual
description, one install command, and the security/authentication caveat. Avoid
keyword stuffing or duplicated marketing copy.

### Round 3 — Package and OCI distribution

Maintain PyPI, Docker Hub, and GHCR as release-backed distribution channels.
For every release:

1. Publish the Python package and verify `uvx openapi-mcp-sdk server` from a
   clean environment.
2. Publish immutable container tags and record the digest in the release
   notes.
3. Update Docker MCP metadata and any registry manifests.
4. Re-test the installation snippets copied into external listings.

### Round 4 — Private and enterprise catalogs

Create an organization-owned OCI catalog for approved internal clients and
enterprise aggregators. The private catalog must pin image digests, define
allowed tools, document token scopes, and include an owner and review date.
Record private catalog URLs as `Private` entries; never publish internal
endpoints or credentials in this file.

### Round 5 — Refresh and traffic measurement

Review all published listings at least monthly and after every release. Track
referral traffic using GitHub Insights, PyPI download statistics, Docker pulls,
registry usage metrics, and listing-specific analytics where available. Keep
the canonical GitHub URL stable so comparisons remain meaningful.

## Submission asset checklist

Before opening a PR or creating a listing, verify:

- [ ] Repository URL, package name, version, license, and description match.
- [ ] `uvx`, `pipx`, `pip`, and Docker commands have been tested cleanly.
- [ ] Transport is stated accurately; do not advertise a remote endpoint that
      has not been deployed and tested.
- [ ] Authentication requirements and token scopes are explicit.
- [ ] No secret, private URL, or production credential appears in metadata.
- [ ] Tool permissions and possible write operations are described cautiously.
- [ ] A maintainer contact and support URL are available.
- [ ] The submission URL, status, date, and review outcome are recorded here.

## Verified submission routes

These routes were checked on 2026-08-07 and should be re-checked before each
submission because external policies can change.

| Target | Verified route | Important prerequisite |
| --- | --- | --- |
| Official MCP Registry | Publish a `server.json` with the registry publisher tooling and namespace authentication. | Decide whether the server is published as a remote HTTPS endpoint, a package, or both; the current repository needs a final manifest. |
| Docker MCP Registry | Open a PR at [`docker/mcp-registry`](https://github.com/docker/mcp-registry). | Provide a working container and choose Docker-built or community-built distribution. |
| Glama | Submit the GitHub repository for indexing. | Glama scans tools, schemas, annotations, license, and quality signals; provide a scan-safe path for authentication. |
| Smithery | Use [`smithery.ai/new`](https://smithery.ai/new) or `smithery mcp publish`. | Requires public Streamable HTTP for remote publishing, and OAuth support when auth is required; an MCPB bundle is an alternative for local distribution. |
| PulseMCP | Use [`pulsemcp.com/submit`](https://www.pulsemcp.com/submit). | Manual submission is available; the directory also imports the Official MCP Registry and enriches listings. |
| Community directories | Follow each repository/site's current PR, issue, or submission form. | Use the same canonical metadata, but tailor the use case and installation instructions to the directory. |

### Product-specific blockers to resolve

- The repository currently ships a package and Docker deployment, but no
  committed Official MCP Registry `server.json` manifest.
- The current documented default is HTTP/SSE on port `8080`; do not claim
  Streamable HTTP or a public remote service until it is implemented and
  deployed.
- The bearer-token forwarding model may not be sufficient for hosted
  directories that require OAuth. Decide whether to add OAuth, provide a
  safe public scan mode, or distribute only the local/container artifact.
- Docker Hub and GHCR image names must be confirmed before publication; record
  the chosen immutable image reference in the release workflow.

## Submission 01 — awesome-mcp

### Maintainer requirements observed

The repository asks contributors to create a pull request or open an issue and
focuses on developer tools, frameworks, and resources relevant to MCP. It is
not limited to executable MCP servers, so the SDK and gateway positioning is a
good fit.

### Proposed listing

```markdown
- [Openapi MCP SDK](https://github.com/openapi/mcp-server) - Official Openapi.com Python SDK and ready-to-run MCP gateway for authenticated Openapi.com APIs. Install with `uvx openapi-mcp-sdk server`, or deploy with Docker; MIT licensed.
```

### Submission action

1. Open a pull request against `eon01/awesome-mcp` and place the entry under
   `Server Frameworks and SDKs` → `Open Source`.
2. If the maintainer prefers issue-first review, open an issue with the same
   proposed listing and link this repository.
3. After merge, replace the placeholder in the tracker with the PR or issue
   URL and set the status to `Published`.

## Submission 02 — awesome-agentic-devops

### Maintainer requirements observed

The catalog requires updates to both `data/repos.yaml` and `README.md`. Entries
are expected to identify a concrete DevOps, Cloud, SRE, Kubernetes, Terraform,
CI/CD, or platform use case, plus action level, approval model, evidence,
risk notes, and an operator note. The maintainers validate the repository URL,
category, and artifact type in CI.

### Proposed catalog record

The exact category slug must be selected from the catalog's current validator
backed slugs during the PR. The following is the submission content; preserve
the cautious labels until the maintainers or a technical review confirm the
tool-level behavior.

```yaml
- name: openapi/mcp-server
  url: https://github.com/openapi/mcp-server
  category: <current-api-or-platform-mcp-category>
  type: mcp-server
  framework: Python + FastMCP + MCP
  primary_language: Python
  cloud_provider: none
  use_cases:
    - authenticated-api-gateway
    - business-api-automation
    - platform-engineering
    - openapi-com-integration
  action_level: write-capable
  human_approval: unknown
  evidence_tracing: partial
  maturity: prototype
  risk_notes: "The gateway forwards client bearer tokens to Openapi.com APIs; scope tokens by least privilege, review tool permissions, and require explicit approval before write-capable operations."
  operator_note: "Official Openapi.com MCP gateway and Python SDK, runnable with uvx or Docker, exposing authenticated API workflows through a standard MCP endpoint."
  labels:
    - mcp
    - approval
    - write
```

The PR should add the entry to the relevant catalog section in `README.md`,
use the repository's current category/type vocabulary, and include the
repository's existing CI or test evidence where requested. Do not claim that
the server is production-ready: the package is currently classified as Beta.

### Submission action

1. Read the current `CONTRIBUTING.md`, validator, and operator-safety checklist
   immediately before opening the PR; these are external and may change.
2. Replace `<current-api-or-platform-mcp-category>` with a valid current slug.
3. Submit one PR changing `data/repos.yaml` and `README.md` together.
4. Record the PR URL, review feedback, merge commit, and publication date here.

## Distribution standards

- Prefer canonical links to this GitHub repository and the PyPI package.
- Use factual descriptions and disclose Beta maturity, authentication, and
  write-capable or client-dependent behavior.
- Never publish credentials, private endpoints, or user-specific tokens.
- Keep installation commands synchronized with `README.md` and `pyproject.toml`.
- Re-check every published listing after releases, package-name changes, or
  protocol/transport changes.
- Track private directories only when their access policy and listing owner are
  known; mark them `Private` and record the contact or submission channel.

## Next execution order

1. Resolve the product-specific blockers in Round 0.
2. Submit Round 1 to the Official MCP Registry, Docker MCP Registry, Glama,
   Smithery, and PulseMCP.
3. Submit Round 2 to the two initial GitHub aggregators, awesome-mcp-servers,
   mcp.so, MCPFind, and mcpservers.org.
4. Complete Round 3 release automation and verify package/container metrics.
5. Create a private OCI catalog and owner policy for Round 4.

## Change log

| Date | Change |
| --- | --- |
| 2026-08-07 | Created the English distribution registry and prepared the first two GitHub aggregator submissions. |
| 2026-08-07 | Expanded the tracker to official, directory, package, OCI, and private catalog channels and added a five-round distribution plan. |
