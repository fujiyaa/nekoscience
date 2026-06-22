CATEGORIES = {
    "general": {
        "title": "settings_category_general",
        "order": 1,
    },
    "/rs": {
        "title": "settings_category_rs",
        "order": 2,
    },
    "/score": {
        "title": "settings_category_score",
        "order": 3,
    },
    "/average": {
        "title": "settings_category_average",
        "order": 4,
    },
    "/music": {
        "title": "settings_category_music",
        "order": 5,
    }

}

SETTINGS = {
    "settings_link_profile_to_card": {
        "default": True,
        "category": "general",
        "ui": "toggle",
    },
    "settings_rs_score_to_card": {
        "default": True,
        "category": "general",
        "ui": "toggle",
    },
    "lang": {
        "default": "ru",
        "category": "general",
        "ui": "select",
    },
   

    "settings_rs_display_fails": {
        "default": True,
        "category": "/rs",
        "ui": "toggle",
    },
    

    "settings_average_recent_display_fails": {
        "default": False,
        "category": "/average",
        "ui": "toggle",
    },

    "settings_scores_display_more_scores": {
        "default": True,
        "category": "/score",
        "ui": "toggle",
    },

    "settings_music_enable_speedup": {
        "default": False,
        "category": "/music",
        "ui": "toggle",
    },
    "settings_music_enable_pitch": {
        "default": False,
        "category": "/music",
        "ui": "toggle",
    },
}