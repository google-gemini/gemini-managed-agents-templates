---
name: product-comparison
description: Compare multiple products using price, specifications, features, requirements, and value. Use this skill when the user asks to compare products or wants to understand differences between product options.
---

# Product Comparison Skill

## Purpose

Compare shortlisted products objectively and identify
the strengths and weaknesses of each option.

## Inputs

Use:

- Product information from research
- User requirements
- Budget
- Required features
- Optional preferences

## Workflow

1. Identify the products being compared.
2. Normalize comparable specifications.
3. Compare each product against the user's requirements.
4. Identify advantages and disadvantages.
5. Identify important differences.
6. Identify missing or unverified information.
7. Produce a structured comparison.

## Comparison Criteria

Compare relevant attributes such as:

- Price
- Performance
- Specifications
- Features
- Build quality
- Battery life
- Warranty
- Availability
- Value for money

Only compare attributes relevant to the product category.

## Rules

Do not assume that a higher specification always means
a better product.

Prioritize the user's requirements.

Clearly distinguish verified information from assumptions.

## Output

Return:

| Product | Price | Key Features | Advantages | Disadvantages |
|---|---:|---|---|---|

Then provide:

### Requirement Match

Explain how each product satisfies the user's
requirements.

### Key Differences

Explain the most important differences between
the products.

Do not make the final recommendation unless
specifically requested.