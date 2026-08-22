---
name: product-recommendation
description: Recommend the product that best matches the user's requirements after considering product research, comparison, price, features, and value. Use this skill when the user asks for the best product or which product they should choose.
---

# Product Recommendation Skill

## Purpose

Select the product that best matches the user's
requirements and explain the decision.

## Inputs

Consider:

- User requirements
- Product research results
- Product comparison results
- Price analysis
- Mandatory requirements
- Optional preferences
- Budget

## Workflow

1. Identify the user's mandatory requirements.
2. Eliminate products that fail mandatory requirements.
3. Compare the remaining products.
4. Consider price and value.
5. Consider important product strengths and weaknesses.
6. Rank the remaining products.
7. Select the best overall match.
8. Explain the reasoning.

## Decision Rules

Prioritize:

1. Mandatory requirements
2. Intended use
3. Budget
4. Important features
5. Performance
6. Reliability
7. Value for money

Do not select a product solely because it is popular,
has the highest specifications, or has the lowest price.

## Recommendation Categories

When useful, provide:

- Best Overall
- Best Budget Option
- Best Performance
- Best Value

Only provide categories that are meaningful for the
user's request.

## Output

Return:

### Best Recommendation

**Product:**

**Price:**

**Why:**

Explain why this product best matches the user's
requirements.

### Alternatives

Provide up to two alternatives and explain when
each alternative would be preferable.

### Trade-offs

Clearly explain the main disadvantages or compromises
of the recommended product.