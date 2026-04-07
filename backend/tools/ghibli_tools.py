from langchain_core.tools import tool

@tool
def get_ghibli_style_guide(category: str):
    """
    Returns specific Ghibli-style guidelines for a category.
    Categories: 'lighting', 'colors', 'nature', 'architecture'.
    """
    guides = {
        "lighting": "Soft, diffused watercolor lighting. Golden hour glows and deep, breathable shadows.",
        "colors": "Lush greens, cerulean skies, and earthy terracottas. Avoid neon or harsh synthetic colors.",
        "nature": "Meadows filled with specific wildflowers, ancient gnarled trees, and moss-covered stones.",
        "architecture": "Whimsical, lived-in structures. Shingle roofs, creeping ivy, and round wooden windows."
    }
    return guides.get(category.lower(), "Focus on hand-painted textures and organic shapes.")

@tool
def youtube_seo_check(title: str):
    """
    Validates if a title is SEO-friendly for Ghibli content.
    """
    if len(title) > 60:
        return "Title is too long. Keep it under 60 characters for better CTR."
    if "Ghibli" not in title and "Studio" not in title:
        return "Consider adding 'Ghibli Style' to the title for better reach."
    return "Title looks excellent and magical!"
