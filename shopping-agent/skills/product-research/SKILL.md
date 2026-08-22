---
name: product-research
description: Research current products based on user requirements such as category, budget, features, brand, and intended use. Use this skill when the user asks to find, discover, search for, or research products.
---

# Product Research Skill

## Purpose

Find relevant and current products that match the user's
shopping requirements.

## Inputs

Extract the following from the user's request:

- Product category
- Budget
- Brand preference
- Required features
- Intended use
- Location or market
- Other constraints

## Workflow

1. Understand the user's requirements.
2. Identify mandatory requirements and optional preferences.
3. Create relevant search queries.
4. Search for current product information.
5. Collect multiple candidate products.
6. Verify important specifications.
7. Check prices against the user's budget.
8. Remove products that clearly fail mandatory requirements.
9. Return a shortlist of suitable products.

## Search Rules

Use available web search tools when current information
is required.

Prefer reliable sources such as:

- Manufacturer websites
- Major retailers
- Trusted technology/product publications

Do not rely on a single source when important information
needs verification.

## Data to Collect

For each candidate product collect:

- Product name
- Brand
- Current price
- Key specifications
- Important features
- Availability when available
- Source

## Constraints

Never invent:

- Prices
- Specifications
- Availability
- Ratings
- Reviews

If information cannot be verified, clearly indicate that
the information is unavailable or unverified.

## Output

Return a structured shortlist of products that satisfy
the user's requirements.

Do not make the final recommendation unless the user
specifically asks for a recommendation.