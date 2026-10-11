#!/usr/bin/env python3
"""Regenerate assets/stats.svg from live GitHub numbers.

Env: GH_TOKEN (a PAT with read:org + repo also counts private work),
     GH_USER (defaults to ZhuchkaTriplesix).
"""
import json
import os
import urllib.parse
import urllib.request

USER = os.environ.get("GH_USER", "ZhuchkaTriplesix")
TOKEN = os.environ["GH_TOKEN"]
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "stats.svg")

TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 850 175" width="100%" height="100%">
  <defs>
    <pattern id="stat-screentone" width="6" height="6" patternUnits="userSpaceOnUse">
      <circle cx="3" cy="3" r="0.8" fill="#ffffff" fill-opacity="0.03" />
    </pattern>
  </defs>

  <style>
    .val {{ font-family: -apple-system, BlinkMacSystemFont, 'Impact', 'Arial Black', monospace; font-size: 28px; font-weight: 900; letter-spacing: 0.5px; }}
    .lbl {{ font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 10px; font-weight: bold; letter-spacing: 1.5px; fill: #72798f; text-transform: uppercase; }}
    .sub {{ font-family: 'JetBrains Mono', monospace; font-size: 9px; font-weight: bold; letter-spacing: 0.5px; }}
    .tag {{ font-family: 'JetBrains Mono', monospace; font-size: 10.5px; fill: #ff4d8d; font-weight: bold; letter-spacing: 1px; }}
  </style>

  <!-- Deep Dark Background -->
  <rect width="850" height="175" fill="#07080c" rx="8" stroke="#1d202e" stroke-width="1.2" />
  <rect width="850" height="175" fill="url(#stat-screentone)" rx="8" />

  <!-- Top Status Bar -->
  <text x="36" y="32" class="tag">[TELEMETRY // ZHUCHKATRIPLESIX]</text>
  <text x="814" y="32" text-anchor="end" font-family="'JetBrains Mono', monospace" font-size="9.5" fill="#4d5366">ALL {orgs} ORGANIZATIONS &amp; PROJECTS SYNCED</text>
  <line x1="36" y1="44" x2="814" y2="44" stroke="#181a26" stroke-width="1" />

  <!-- 4 Columns Grid with Spacious Padding -->

  <!-- Column 1: Commits -->
  <g transform="translate(36, 68)">
    <text y="0" class="lbl">TOTAL COMMITS</text>
    <text y="38" class="val" fill="#f0f2f8">{commits}</text>
    <text y="58" class="sub" fill="#ff4d8d">PUBLIC COMMITS</text>
  </g>

  <!-- Vertical Divider 1 -->
  <line x1="226" y1="64" x2="226" y2="136" stroke="#181a26" stroke-width="1" />

  <!-- Column 2: Organizations -->
  <g transform="translate(248, 68)">
    <text y="0" class="lbl">ORGANIZATIONS</text>
    <text y="38" class="val" fill="#00f5d4">{orgs}</text>
    <text y="58" class="sub" fill="#63697e">AFFILIATED BODIES</text>
  </g>

  <!-- Vertical Divider 2 -->
  <line x1="422" y1="64" x2="422" y2="136" stroke="#181a26" stroke-width="1" />

  <!-- Column 3: Total Repositories (Personal + Orgs) -->
  <g transform="translate(444, 68)">
    <text y="0" class="lbl">TOTAL REPOS</text>
    <text y="38" class="val" fill="#ff4d8d">{repos}</text>
    <text y="58" class="sub" fill="#63697e">{user_repos} USER • {org_repos} ORGS</text>
  </g>

  <!-- Vertical Divider 3 -->
  <line x1="634" y1="64" x2="634" y2="136" stroke="#181a26" stroke-width="1" />

  <!-- Column 4: Pull Requests -->
  <g transform="translate(656, 68)">
    <text y="0" class="lbl">PULL REQUESTS</text>
    <text y="38" class="val" fill="#f0f2f8">{prs}</text>
    <text y="58" class="sub" fill="#63697e">REVIEWS &amp; MERGES</text>
  </g>
</svg>"""


def call(url, data=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode() if data else None,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def search_total(kind, q):
    return call(f"https://api.github.com/search/{kind}?per_page=1&q={urllib.parse.quote(q)}")["total_count"]


def main():
    commits = search_total("commits", f"author:{USER}")
    prs = search_total("issues", f"author:{USER} type:pr")
    gql = call(
        "https://api.github.com/graphql",
        {
            "query": """query($u:String!){user(login:$u){
                repositories(ownerAffiliations:OWNER){totalCount}
                organizations(first:100){totalCount nodes{repositories{totalCount}}}}}""",
            "variables": {"u": USER},
        },
    )["data"]["user"]
    user_repos = gql["repositories"]["totalCount"]
    org_repos = sum(o["repositories"]["totalCount"] for o in gql["organizations"]["nodes"])
    svg = TEMPLATE.format(
        commits=f"{commits:,}",
        prs=f"{prs:,}",
        orgs=gql["organizations"]["totalCount"],
        repos=user_repos + org_repos,
        user_repos=user_repos,
        org_repos=org_repos,
    )
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"commits={commits} prs={prs} user_repos={user_repos} org_repos={org_repos}")


if __name__ == "__main__":
    main()
