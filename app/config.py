# app/config.py
import os

DB_URL = os.getenv("DATABASE_URL", "sqlite:////app/db/studyplan.db")
API_KEY = os.getenv("API_KEY", "dummy")  # из env, не хардкодим
LOG_MASK_FIELDS = ["password", "token", "secret"]


def mask_sensitive(data: dict) -> dict:
    return {k: ("****" if k.lower() in LOG_MASK_FIELDS else v) for k, v in data.items()}
