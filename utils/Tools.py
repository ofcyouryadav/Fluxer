import discord
from discord.ext import commands
from functools import wraps

def blacklist_check():
    """Decorator to check if a user is blacklisted"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def ignore_check():
    """Decorator to check if a channel is ignored"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator
