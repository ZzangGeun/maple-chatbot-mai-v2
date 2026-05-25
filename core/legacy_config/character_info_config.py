# Configuration for the character info module
import os
from pathlib import Path
from django.core.cache import cache
from django.conf import settings
from character_info.get_character_info import get_character_data
