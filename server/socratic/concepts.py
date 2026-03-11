"""Concept definitions for Socratic tutoring.

Each concept includes structured knowledge the LLM uses for context:
- Key ideas and common misconceptions
- Diagnostic questions and scaffolding hints
- The "aha moment" the tutor is guiding toward
"""

from dataclasses import dataclass


@dataclass
class ConceptDefinition:
    """A teachable concept with pedagogical metadata."""
    id: str
    name: str
    description: str
    key_ideas: list[str]
    common_misconceptions: list[str]
    aha_moment: str
    diagnostic_questions: list[str]
    scaffolding_hints: list[str]

    @property
    def context(self) -> str:
        """Format concept as context string for LLM prompts."""
        ideas = "\n".join(f"  - {idea}" for idea in self.key_ideas)
        misconceptions = "\n".join(f"  - {m}" for m in self.common_misconceptions)
        return (
            f"Topic: {self.name}\n"
            f"Description: {self.description}\n\n"
            f"Key ideas the student should discover:\n{ideas}\n\n"
            f"Common misconceptions to watch for:\n{misconceptions}\n\n"
            f"The 'aha moment': {self.aha_moment}"
        )


CONCEPTS: dict[str, ConceptDefinition] = {
    "division_by_zero": ConceptDefinition(
        id="division_by_zero",
        name="Division by Zero",
        description="Why can't we divide by zero?",
        key_ideas=[
            "Division is the inverse of multiplication: a ÷ b = c means b × c = a",
            "As the divisor approaches zero, the quotient grows without bound",
            "There is no number that, when multiplied by zero, gives a non-zero result",
            "Division by zero is undefined, not infinity — it's a different concept",
            "Computers handle this as an error to prevent crashes",
        ],
        common_misconceptions=[
            "Dividing by zero gives zero",
            "Dividing by zero gives infinity",
            "It's just a rule teachers made up",
            "The answer is 'error' because calculators aren't smart enough",
        ],
        aha_moment="If 10 ÷ 0 = something, then 0 × something = 10, but 0 times anything is 0, so no answer works.",
        diagnostic_questions=[
            "What does division actually mean?",
            "What happens when you divide 10 by smaller and smaller numbers?",
            "If a ÷ b = c, what's another way to write that using multiplication?",
        ],
        scaffolding_hints=[
            "Try concrete examples: 10÷5=2, 10÷2=5, 10÷1=10, 10÷0.5=20...",
            "Connect to multiplication: if the answer is X, then 0 × X should equal 10",
            "Think about sharing cookies among friends — what if there are zero friends?",
        ],
    ),
    "photosynthesis": ConceptDefinition(
        id="photosynthesis",
        name="Photosynthesis",
        description="How do plants make food from sunlight?",
        key_ideas=[
            "Plants convert light energy into chemical energy (glucose)",
            "The inputs are carbon dioxide (CO₂) + water (H₂O) + sunlight",
            "The outputs are glucose (C₆H₁₂O₆) + oxygen (O₂)",
            "Chlorophyll in leaves absorbs light (which is why leaves are green)",
            "This process is the foundation of most food chains on Earth",
        ],
        common_misconceptions=[
            "Plants get food from the soil through their roots",
            "Plants eat sunlight directly as food",
            "Oxygen is the main purpose of photosynthesis (it's a byproduct)",
            "Photosynthesis only happens during the day (true, but cellular respiration happens 24/7)",
        ],
        aha_moment="Plants are actually making sugar out of air and water, using sunlight as the energy source — they're like tiny solar-powered sugar factories.",
        diagnostic_questions=[
            "Where do you think plants get their food?",
            "What do plants need to survive?",
            "Why are most leaves green?",
        ],
        scaffolding_hints=[
            "Think about what goes INTO the plant vs what comes OUT",
            "When you eat food, you get energy. How does a plant get its energy?",
            "The word 'photo' means light, 'synthesis' means putting together...",
        ],
    ),
    "gravity": ConceptDefinition(
        id="gravity",
        name="Gravity",
        description="Why do things fall down?",
        key_ideas=[
            "Every object with mass attracts every other object with mass",
            "The more mass an object has, the stronger its gravitational pull",
            "Earth's gravity pulls everything toward its center",
            "Gravity gets weaker with distance (inverse square law)",
            "Gravity is what keeps planets orbiting the sun and the moon orbiting Earth",
        ],
        common_misconceptions=[
            "Heavier objects fall faster than lighter ones (Galileo disproved this)",
            "There's no gravity in space (there is — it's what keeps satellites orbiting)",
            "Gravity only pulls things down (it pulls in all directions, toward center of mass)",
            "Gravity is a force that only Earth has",
        ],
        aha_moment="YOU are pulling on the Earth just as much as it's pulling on you — but because the Earth is so massive, only you move noticeably.",
        diagnostic_questions=[
            "Why do you think things fall when you drop them?",
            "If you dropped a bowling ball and a tennis ball at the same time, which hits the ground first?",
            "Does gravity exist on the moon? In space?",
        ],
        scaffolding_hints=[
            "Think about magnets — they pull without touching. Gravity is similar but works with mass.",
            "What would happen if Earth had twice as much mass?",
            "Astronauts float in the space station — but is gravity really gone there?",
        ],
    ),
    "fractions": ConceptDefinition(
        id="fractions",
        name="Fractions",
        description="What does 1/2 really mean?",
        key_ideas=[
            "A fraction represents a part of a whole",
            "The denominator tells how many equal parts the whole is divided into",
            "The numerator tells how many of those parts we have",
            "Equivalent fractions look different but represent the same amount (1/2 = 2/4)",
            "Fractions can be greater than 1 (improper fractions like 3/2)",
        ],
        common_misconceptions=[
            "A bigger denominator means a bigger fraction (1/8 > 1/4 because 8 > 4)",
            "You can't have a fraction bigger than 1",
            "Fractions are only about pizza slices",
            "1/3 + 1/3 = 2/6 (adding numerators AND denominators)",
        ],
        aha_moment="The denominator is like a zoom level — the bigger it is, the smaller each piece gets. 1/8 of a pizza is a tiny sliver, even though 8 is bigger than 4.",
        diagnostic_questions=[
            "If you cut a pizza into 4 equal slices, what fraction is one slice?",
            "Which is bigger: 1/4 or 1/8? Why?",
            "Can a fraction be bigger than 1?",
        ],
        scaffolding_hints=[
            "Draw a picture — divide a rectangle into equal parts",
            "Think about sharing fairly: 1/2 means 1 thing shared by 2 people",
            "Compare: would you rather have 1/4 of a cake or 1/8 of a cake?",
        ],
    ),
    "water_cycle": ConceptDefinition(
        id="water_cycle",
        name="Water Cycle",
        description="Where does rain come from?",
        key_ideas=[
            "Water continuously cycles: evaporation → condensation → precipitation → collection",
            "The sun's heat drives evaporation from oceans, lakes, and rivers",
            "Water vapor rises, cools, and condenses into clouds (tiny water droplets)",
            "When droplets combine and get heavy enough, they fall as precipitation",
            "The total amount of water on Earth stays roughly the same — it just changes form",
        ],
        common_misconceptions=[
            "Clouds are made of water vapor (they're actually tiny liquid droplets or ice)",
            "Rain comes from clouds 'breaking open'",
            "New water is created when it rains",
            "Evaporation only happens when water boils",
        ],
        aha_moment="The water you drink today might have been in a dinosaur's lake millions of years ago — water is constantly recycled, never created or destroyed.",
        diagnostic_questions=[
            "Where do you think rain comes from?",
            "What happens to a puddle on a hot day?",
            "What are clouds made of?",
        ],
        scaffolding_hints=[
            "Think about what happens to water in a pot on the stove — where does the steam go?",
            "Have you ever seen water droplets on a cold glass? Why does that happen?",
            "If the sun heats the ocean, where does that water go?",
        ],
    ),
}


def get_concept(concept_id: str) -> ConceptDefinition | None:
    """Look up a concept by ID."""
    return CONCEPTS.get(concept_id)


def list_concepts() -> list[dict]:
    """Return a list of concept summaries."""
    return [
        {"id": c.id, "name": c.name, "description": c.description}
        for c in CONCEPTS.values()
    ]
