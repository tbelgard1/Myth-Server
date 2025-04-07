"""
Core utility functions for the Myth metaserver.

Provides common constants, type aliases, and utility functions for:
- Fixed point math
- Bit manipulation 
- String manipulation
- Network byte order conversion
"""

import time
import socket
import struct
from typing import Union, TypeVar, Any
from dataclasses import dataclass
from enum import IntEnum, auto

# Constants
TRUE = 1
FALSE = 0
NONE = -1

KILO = 1024
MEG = KILO * KILO
GIG = KILO * MEG

MACHINE_TICKS_PER_SECOND = 1

# Fixed point math constants
FIXED_FRACTIONAL_BITS = 16
FIXED_ONE = 1 << FIXED_FRACTIONAL_BITS
FIXED_ONE_HALF = FIXED_ONE // 2

SHORT_FIXED_FRACTIONAL_BITS = 8
SHORT_FIXED_ONE = 1 << SHORT_FIXED_FRACTIONAL_BITS
SHORT_FIXED_ONE_HALF = SHORT_FIXED_ONE // 2

# Type aliases
word = int  # unsigned short
byte = int  # unsigned char
boolean = int  # int
fixed = int  # long
fixed_fraction = int  # unsigned short
short_fixed = int  # short
short_fixed_fraction = int  # unsigned char

# Type variables for generic functions
T = TypeVar('T', int, float)

def machine_tick_count() -> int:
    """Get current time in seconds since epoch"""
    return int(time.time())

def sgn(x: Union[int, float]) -> int:
    """Return sign of number (-1, 0, or 1)"""
    return (x > 0) - (x < 0)

def abs_val(x: T) -> T:
    """Return absolute value"""
    return abs(x)

def min_val(a: T, b: T) -> T:
    """Return minimum of two values"""
    return min(a, b)

def max_val(a: T, b: T) -> T:
    """Return maximum of two values"""
    return max(a, b)

def floor_val(n: T, floor: T) -> T:
    """Return n if >= floor, otherwise floor"""
    return max(n, floor)

def ceiling_val(n: T, ceiling: T) -> T:
    """Return n if <= ceiling, otherwise ceiling"""
    return min(n, ceiling)

def pin(n: T, floor: T, ceiling: T) -> T:
    """Pin value between floor and ceiling"""
    return min(max(n, floor), ceiling)

def flag(b: int) -> int:
    """Create bit flag"""
    return 1 << b

def flag_range(first_bit: int, last_bit: int) -> int:
    """Create bit flag range"""
    return ((1 << (last_bit + 1 - first_bit)) - 1) << first_bit

def is_flagged(var: int, flag: int) -> bool:
    """Check if flag is set"""
    return bool(var & flag)

def set_flag(var: int, flag: int) -> int:
    """Set flag"""
    return var | flag

def remove_flag(var: int, flag: int) -> int:
    """Remove flag"""
    return var & ~flag

def toggle_flag(var: int, flag: int) -> int:
    """Toggle flag"""
    return var ^ flag

def high_word(n: int) -> int:
    """Get high word (upper 16 bits)"""
    return (n >> 16) & 0xffff

def low_word(n: int) -> int:
    """Get low word (lower 16 bits)"""
    return n & 0xffff

# Fixed point math functions
def fixed_to_short_fixed(f: fixed) -> short_fixed:
    """Convert from 16.16 to 8.8 fixed point"""
    return f >> (FIXED_FRACTIONAL_BITS - SHORT_FIXED_FRACTIONAL_BITS)

def short_fixed_to_fixed(f: short_fixed) -> fixed:
    """Convert from 8.8 to 16.16 fixed point"""
    return f << (FIXED_FRACTIONAL_BITS - SHORT_FIXED_FRACTIONAL_BITS)

def fixed_to_float(f: fixed) -> float:
    """Convert from fixed point to float"""
    return f / FIXED_ONE

def float_to_fixed(f: float) -> fixed:
    """Convert from float to fixed point"""
    return int(f * FIXED_ONE)

def integer_to_fixed(s: int) -> fixed:
    """Convert from integer to fixed point"""
    return s << FIXED_FRACTIONAL_BITS

def fixed_to_integer(f: fixed) -> int:
    """Convert from fixed point to integer"""
    return f >> FIXED_FRACTIONAL_BITS

def fixed_to_integer_round(f: fixed) -> int:
    """Convert from fixed point to integer with rounding"""
    return fixed_to_integer(f + FIXED_ONE_HALF)

def fixed_fractional_part(f: fixed) -> fixed:
    """Get fractional part of fixed point number"""
    return f & (FIXED_ONE - 1)

def short_fixed_to_float(f: short_fixed) -> float:
    """Convert from short fixed point to float"""
    return f / SHORT_FIXED_ONE

def float_to_short_fixed(f: float) -> short_fixed:
    """Convert from float to short fixed point"""
    return int(f * SHORT_FIXED_ONE)

def integer_to_short_fixed(s: int) -> short_fixed:
    """Convert from integer to short fixed point"""
    return s << SHORT_FIXED_FRACTIONAL_BITS

def short_fixed_to_integer(f: short_fixed) -> int:
    """Convert from short fixed point to integer"""
    return f >> SHORT_FIXED_FRACTIONAL_BITS

def short_fixed_to_integer_round(f: short_fixed) -> int:
    """Convert from short fixed point to integer with rounding"""
    return short_fixed_to_integer(f + SHORT_FIXED_ONE_HALF)

def short_fixed_fractional_part(f: short_fixed) -> short_fixed:
    """Get fractional part of short fixed point number"""
    return f & (SHORT_FIXED_ONE - 1)

# String manipulation functions
def strupr(string: str) -> str:
    """Convert string to uppercase"""
    return string.upper()

def strnupr(string: str, n: int) -> str:
    """Convert first n characters of string to uppercase"""
    return string[:n].upper() + string[n:]

def strlwr(string: str) -> str:
    """Convert string to lowercase"""
    return string.lower()

def strnlwr(string: str, n: int) -> str:
    """Convert first n characters of string to lowercase"""
    return string[:n].lower() + string[n:]

# Network byte order functions
def ntohl(x: int) -> int:
    """Convert 32-bit integer from network to host byte order"""
    return socket.ntohl(x)

def htonl(x: int) -> int:
    """Convert 32-bit integer from host to network byte order"""
    return socket.htonl(x)

def ntohs(x: int) -> int:
    """Convert 16-bit integer from network to host byte order"""
    return socket.ntohs(x)

def htons(x: int) -> int:
    """Convert 16-bit integer from host to network byte order"""
    return socket.htons(x)
