---
name: price-analysis
description: Analyze product prices, budgets, discounts, price differences, and value for money. Use this skill when the user asks whether a product is affordable, worth the price, discounted, or good value.
---

# Price Analysis Skill

## Purpose

Analyze product pricing and determine how well products
fit within the user's budget.

## Inputs

Extract:

- User budget
- Product price
- Multiple product prices
- Discount information
- Required features
- Product value

## Workflow

1. Identify the user's maximum budget.
2. Collect current product prices.
3. Calculate the difference between price and budget.
4. Compare prices between shortlisted products.
5. Analyze whether additional cost provides meaningful benefits.
6. Identify potential discounts when reliable information
   is available.
7. Determine relative value for money.

## Calculations

When appropriate calculate:

- Price difference
- Percentage difference
- Budget remaining
- Discount percentage

Use exact arithmetic when calculations are required.

## Rules

Do not claim that a product is discounted unless the
discount can be verified.

Do not assume historical prices.

Do not recommend a more expensive product solely because
it has a higher price.

Consider the user's requirements when determining value.

## Output

Provide:

- Current price
- User budget
- Budget difference
- Price comparison
- Important benefits of paying more
- Value assessment

Clearly state when historical or discount information
cannot be verified.