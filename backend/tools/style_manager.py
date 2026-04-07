STYLE_REGISTRY = {
    "ghibli": {
        "name": "Ghibli Classic",
        "narrative_persona": "a visionary Studio Ghibli creative director. Capture quiet, awe-inspiring, and slightly melancholic essence.",
        "visual_rules": "Studio Ghibli art style, soft watercolor lighting, lush backgrounds, whimsical details, hand-drawn texture.",
        "music_moods": {
            "adventure": "whimsical_adventure",
            "emotional": "nostalgic_memory",
            "magical": "magical_wonder"
        }
    },
    "cyberpunk": {
        "name": "Neon Cyberpunk",
        "narrative_persona": "a gritty Cyberpunk world-builder. Focus on high-tech, low-life, rain-slicked streets, and neon-lit corporate spires.",
        "visual_rules": "Cyberpunk 2077 aesthetic, blade runner lighting, neon glows, rainy streets, cinematic high-contrast, futuristic tech, synth-wave atmosphere.",
        "music_moods": {
            "adventure": "triumphant_heroic",
            "emotional": "melancholy_sorrow",
            "magical": "mysterious_forest"
        }
    },
    "shinkai": {
        "name": "Shinkai Realism",
        "narrative_persona": "a poetic director like Makoto Shinkai. Focus on distance, longing, and the breathtaking beauty of everyday life.",
        "visual_rules": "Makoto Shinkai art style (Your Name), hyper-realistic skies, dramatic sunbeams, lens flares, emotional lighting, vibrant blue and purple palettes.",
        "music_moods": {
            "adventure": "magical_wonder",
            "emotional": "nostalgic_memory",
            "magical": "peaceful_watercolor"
        }
    },
    "disney": {
        "name": "Disney Magic",
        "narrative_persona": "a classic Disney animator. Focus on optimism, heartwarming humor, and timeless fairytale wonder.",
        "visual_rules": "Classic Disney 2D animation style, traditional hand-drawn look, storybook magic, vibrant and friendly colors, expressive characters.",
        "music_moods": {
            "adventure": "whimsical_adventure",
            "emotional": "magical_wonder",
            "magical": "triumphant_heroic"
        }
    },
    "spiderverse": {
        "name": "Comic Fusion",
        "narrative_persona": "a boundary-pushing comic director. Focus on high energy, urban grit, and multi-dimensional chaos.",
        "visual_rules": "Into the Spider-Verse style, comic book textures, half-tone dots, vibrant chromatic aberration, stylized street art, dynamic action frames.",
        "music_moods": {
            "adventure": "triumphant_heroic",
            "emotional": "mysterious_forest",
            "magical": "spooky_shadows"
        }
    }
}

def get_style_data(style_id: str):
    """Returns the DNA for the requested universe."""
    return STYLE_REGISTRY.get(style_id, STYLE_REGISTRY["ghibli"])
