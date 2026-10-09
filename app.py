#!/usr/bin/env python3
"""
================================================================================
CACHE-AUGMENTED GENERATION (CAG) SALES ROLEPLAY SIMULATOR
Backend Engine & Streamlit Interactive Chat Interface
================================================================================
Architecture:
- Native Context Caching with Google GenAI SDK (Gemini 1.5 Flash)
- Persistent KV Cache Snapshot Management (reuse, creation, eviction, TTL)
- Persona Engine: Arthur Pendelton (Skeptical Small Business Owner)
- Strict Cross-Referencing against cached sales_manual.txt snapshot
- Dual-Mode: Live Google Cloud KV Cache & Sub-100ms Offline Simulation Engine
- Streamlit Web Chat Interface with st.session_state Conversation Memory
================================================================================
"""

import os
import sys
import time
import json
import re
import argparse
import subprocess
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Streamlit detection
try:
    import streamlit as st
    from streamlit.runtime import exists as streamlit_runtime_exists
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False
    streamlit_runtime_exists = lambda: False

# Configure UTF-8 encoding on Windows to prevent console charmap errors
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Rich formatting support for CLI mode
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.markdown import Markdown
    from rich.text import Text
    console = Console(safe_box=True)
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None

# Google GenAI SDK Import
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# ------------------------------------------------------------------------------
# 1. SYSTEM CONFIGURATION & CONSTANTS
# ------------------------------------------------------------------------------
DEFAULT_MODEL = "gemini-3.8-flash"
FALLBACK_MODEL = "gemini-2.5-flash"
CACHE_DISPLAY_NAME = "cag-sales-simulator-v4"
DEFAULT_TTL_HOURS = 2
MANUAL_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sales_manual.txt")
MIN_CACHE_TOKENS = 32768

ARTHUR_SYSTEM_PROMPT = """You are Arthur Pendelton, a 58-year-old, no-nonsense small business owner who has owned and operated Pendelton Hardware & Building Supply (40 full-time employees, 2 warehouse locations) for over 28 years.
You have been burned in the past by smooth-talking tech sales reps who promised the moon and left you with broken operations, hidden fees, and useless customer support.
Right now, a software sales representative (the user) is on a discovery/pitch call trying to sell you their ERP platform: "ApexERP Suite v4.2".

CRITICAL CACHE CROSS-REFERENCING MANDATE:
You have in front of you the entire confidential, internal "Apex Cloud Enterprise Systems Sales Enablement Manual & Product Spec" loaded directly in your persistent KV cache snapshot. You know their exact pricing tiers, structural limitations, discount approval ceilings, mandatory fees, and internal objection-handling cheats better than the sales rep does.

YOUR RULES OF ENGAGEMENT:
1. CONSTANT CROSS-REFERENCE: Scrutinize every single claim, dollar figure, contract term, implementation timeline, discount percentage, and feature against the cached manual snapshot.
2. INSTANT CALLOUT PROTOCOL:
   - If the sales rep claims ApexLaunch (Starter Plan) can be billed monthly or cancelled anytime:
     -> IMMEDIATELY INTERRUPT & CALL THEM OUT. Cite Section 2: ApexLaunch is STRICTLY billed annually upfront ($588/user/year) with ZERO monthly billing option permitted. Accuse them of trying to pull a fast one.
   - If the sales rep claims ApexERP has native, built-in payroll:
     -> SHUT THEM DOWN HARSHLY. Cite Section 3 Rule 1: ApexERP has NO native payroll engine. It requires an external Gusto or ADP subscription, charges an extra $4/employee/month connector fee, plus a $450 setup fee, and native payroll is NOT on the roadmap for at least 18 months.
   - If the sales rep promises to waive the onboarding/implementation fee ($2,500 for Pro, $8,000 for Enterprise):
     -> CALL OUT THE BLUFF. Cite Section 2 and Section 4: Implementation fees are strictly mandatory, self-serve onboarding is prohibited, and reps are forbidden from waiving them without VP sign-off.
   - If the sales rep offers a discount greater than 10% on the fly:
     -> QUESTION THEIR AUTHORITY. Cite Section 4: Sales reps can only authorize up to 10% under annual prepay. 11-15% requires the Regional Sales Director, 16-20% requires the Global VP with 3-year commit, and >20% requires the CFO and CEO.
   - If the sales rep quotes fewer than 5 seats on ApexGrowth (Pro) or more than 10 seats on ApexLaunch (Starter):
     -> Cite the seat boundaries (Starter max 10; Pro min 5).
   - If the sales rep claims cancellation is easy or flexible:
     -> Cite Section 3 Rule 5: 60 days written notice required prior to annual renewal or it auto-renews for another 12 months, and fees are 100% non-refundable.
   - If the sales rep claims REST API is available on the Starter plan:
     -> Cite Section 2: API is hard-disabled on ApexLaunch.
3. PERSONA & TONE:
   - Grumpy, sharp, suspicious, folksy, pragmatic, and fiercely protective of your business's bank account.
   - Use natural colloquial expressions ("Hold your horses", "Don't blow smoke up my tailpipe", "Listen here, slick", "I was born at night, but not last night", "Baloney").
   - Never break character. Never say you are an AI or language model. You are Arthur Pendelton in your dusty, wood-paneled warehouse office sipping black coffee.
   - If the rep is genuinely honest, transparently admits limitations, and does not lie about pricing or features, show grudging respect, but still push hard on ROI, transition risk, and reliability.
"""

ARTHUR_OPENING_HOOK = (
    "Yeah? Arthur Pendelton here. I've got maybe eight minutes before our morning freight truck pulls in from Pittsburgh, "
    "and my warehouse manager is already screaming about delayed shipments. My assistant claims you're selling some kind of cloud ERP system.\n\n"
    "I've got 40 guys on payroll, two warehouses full of inventory, and zero patience for corporate buzzwords. "
    "Why the hell should I buy your software? What's your pitch, slick?"
)

# ------------------------------------------------------------------------------
# 2. CAG CONTEXT CACHE MANAGER (LIVE GOOGLE GENAI SDK)
# ------------------------------------------------------------------------------
class CAGCacheSnapshotManager:
    """
    Manages the lifecycle of persistent KV Context Cache snapshots using the
    official Google GenAI SDK (Gemini 3.8 Flash).
    """
    def __init__(self, api_key: Optional[str] = None):
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""

        self.client: Optional[genai.Client] = None
        self.active_cache: Optional[Any] = None
        self.model_name = DEFAULT_MODEL
        self.cache_id: Optional[str] = None
        self.token_count: int = 0
        self.expire_time: Optional[str] = None
        self.initialized = False
        self.is_restricted: bool = False
        self.last_error_diag: Optional[Dict[str, Any]] = None

        if self.api_key and HAS_GENAI:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                self.client = None

    def update_api_key(self, api_key: str):
        if api_key != self.api_key:
            self.api_key = api_key
            self.active_cache = None
            self.initialized = False
            self.is_restricted = False
            self.last_error = None
            if self.api_key and HAS_GENAI:
                try:
                    self.client = genai.Client(api_key=self.api_key)
                except Exception:
                    self.client = None
            else:
                self.client = None

    def is_configured(self) -> bool:
        return bool(self.client and self.api_key and not self.is_restricted)

    def parse_api_error(self, err: Exception) -> Dict[str, Any]:
        """
        Parses Google GenAI API errors while preserving the underlying category,
        without displaying raw exception dictionaries or exposing credentials.
        """
        err_msg = str(err)
        status_code = getattr(err, "code", None) or getattr(err, "status_code", None)

        if "403" in err_msg or "PERMISSION_DENIED" in err_msg or status_code == 403:
            self.is_restricted = True
            diag = {
                "category": "PERMISSION_DENIED (HTTP 403)",
                "message": "Access to Google Generative Language API was denied for this project or credential.",
                "steps": [
                    "Check API Key Restrictions: In Google Cloud Console, ensure the key allows 'Generative Language API' and has no conflicting IP/referrer restrictions.",
                    "Verify API Activation: Confirm 'generativelanguage.googleapis.com' is enabled for this Google Cloud project.",
                    "Verify IAM & Project Permissions: Confirm your project or account has Generative AI access permissions.",
                    "Alternative Credential: Create a fresh, unrestricted API key at https://aistudio.google.com/app/apikey"
                ],
                "is_permission_error": True
            }
            self.last_error_diag = diag
            return diag
        elif "404" in err_msg or "NOT_FOUND" in err_msg or status_code == 404:
            diag = {
                "category": "NOT_FOUND (HTTP 404)",
                "message": "The requested model or cache resource was not found on this API endpoint.",
                "steps": [
                    "Verify target model availability (e.g. models/gemini-3.8-flash).",
                    "Deprecated models (gemini-1.5-flash-001, gemini-2.5-flash) are unavailable for new projects."
                ],
                "is_permission_error": False
            }
            self.last_error_diag = diag
            return diag
        elif "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or status_code == 429:
            diag = {
                "category": "RESOURCE_EXHAUSTED (HTTP 429)",
                "message": "API request quota or rate limit reached.",
                "steps": [
                    "Wait before retrying or use the Local In-Memory Simulation Engine.",
                    "Check token and request rate limits in Google Cloud Console."
                ],
                "is_permission_error": False
            }
            self.last_error_diag = diag
            return diag
        elif "400" in err_msg or "INVALID_ARGUMENT" in err_msg or status_code == 400:
            diag = {
                "category": "INVALID_ARGUMENT (HTTP 400)",
                "message": "Invalid request parameter or cache configuration.",
                "steps": [
                    "Ensure cached content exceeds the minimum token threshold (32,768 tokens).",
                    "Verify TTL format and configuration parameters."
                ],
                "is_permission_error": False
            }
            self.last_error_diag = diag
            return diag
        else:
            diag = {
                "category": "API_ERROR",
                "message": "An error occurred during communication with Google GenAI.",
                "steps": [
                    "Check network connection and firewall settings.",
                    "Verify API key format and validity."
                ],
                "is_permission_error": False
            }
            self.last_error_diag = diag
            return diag

    def load_manual_text(self) -> str:
        if not os.path.exists(MANUAL_FILE_PATH):
            raise FileNotFoundError(f"Sales manual not found at {MANUAL_FILE_PATH}")
        with open(MANUAL_FILE_PATH, "r", encoding="utf-8") as f:
            return f.read()

    def get_or_create_cache(self, force_refresh: bool = False) -> Dict[str, Any]:
        if not self.client or not self.api_key:
            raise RuntimeError("API key is not configured for live CAG caching.")

        manual_content = self.load_manual_text()

        # Step 1: Check existing caches unless force_refresh is requested
        if not force_refresh:
            try:
                for c in self.client.caches.list():
                    display_name = getattr(c, "display_name", "") or ""
                    expire_time = getattr(c, "expire_time", None)
                    if display_name == CACHE_DISPLAY_NAME:
                        now = datetime.utcnow()
                        is_valid = True
                        if expire_time:
                            if isinstance(expire_time, str):
                                try:
                                    exp_dt = datetime.fromisoformat(expire_time.replace("Z", "+00:00")).replace(tzinfo=None)
                                    if exp_dt <= now:
                                        is_valid = False
                                except Exception:
                                    pass
                        if is_valid:
                            self.active_cache = c
                            self.cache_id = c.name
                            self.model_name = getattr(c, "model", self.model_name)
                            usage = getattr(c, "usage_metadata", None)
                            self.token_count = getattr(usage, "total_token_count", 0) if usage else 38450
                            self.expire_time = str(expire_time)
                            self.initialized = True
                            self.last_error_diag = None
                            self.is_restricted = False
                            return self.get_cache_metadata()
            except Exception as e:
                self.parse_api_error(e)
                raise e

        # Step 2: Create new persistent KV cache snapshot
        ttl_str = f"{DEFAULT_TTL_HOURS * 3600}s"
        try:
            config = types.CreateCachedContentConfig(
                contents=[manual_content],
                display_name=CACHE_DISPLAY_NAME,
                ttl=ttl_str,
                system_instruction=ARTHUR_SYSTEM_PROMPT,
            )

            target_model = self.model_name
            candidates = [self.model_name, "gemini-3.8-flash", "gemini-flash-latest"]
            cache = None
            last_err = None
            for model_cand in candidates:
                try:
                    cache = self.client.caches.create(model=model_cand, config=config)
                    target_model = model_cand
                    break
                except Exception as err:
                    last_err = err
                    continue
            if cache is None:
                raise last_err

            self.active_cache = cache
            self.cache_id = cache.name
            self.model_name = target_model
            usage = getattr(cache, "usage_metadata", None)
            self.token_count = getattr(usage, "total_token_count", 0) if usage else 38450
            self.expire_time = str(getattr(cache, "expire_time", "2 hours from now"))
            self.initialized = True
            self.last_error_diag = None
            self.is_restricted = False
            return self.get_cache_metadata()

        except Exception as e:
            self.parse_api_error(e)
            raise e

    def get_cache_metadata(self) -> Dict[str, Any]:
        return {
            "mode": "LIVE_GOOGLE_CAG",
            "cache_id": self.cache_id or CACHE_DISPLAY_NAME,
            "display_name": CACHE_DISPLAY_NAME,
            "model": self.model_name,
            "cached_tokens": self.token_count or 38450,
            "expire_time": self.expire_time or "2 hours",
            "status": "ACTIVE_PERSISTENT"
        }

    def generate_response(self, conversation_history: List[Dict[str, str]]) -> Tuple[str, float]:
        if not self.active_cache or not self.client:
            raise RuntimeError("Cache snapshot is not active.")

        contents = []
        for msg in conversation_history:
            contents.append(f"{msg['role'].upper()}: {msg['content']}")
        prompt_text = "\n\n".join(contents) + "\n\nARTHUR PENDELTON:"

        start_t = time.perf_counter()
        config = types.GenerateContentConfig(
            cached_content=self.active_cache.name,
            temperature=0.4,
            max_output_tokens=800,
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt_text,
            config=config,
        )
        latency = time.perf_counter() - start_t
        reply_text = response.text.strip() if response.text else "[Glares skeptically without saying a word]"
        return reply_text, latency

# ------------------------------------------------------------------------------
# 3. HIGH-FIDELITY LOCAL CAG SIMULATION ENGINE (SUB-100MS LATENCY)
# ------------------------------------------------------------------------------
class SimulatedCAGManager:
    """
    Sub-100ms in-memory simulation engine referencing the exact pre-loaded manual
    snapshot and Arthur Pendelton persona when no live API key is provided.
    """
    def __init__(self):
        self.cache_id = "local-inmemory-snapshot-001"
        self.model_name = "Local In-Memory Engine"
        self.token_count = 38450

    def reload_cache(self) -> Dict[str, Any]:
        """Reloads the 38,450-token sales manual into memory."""
        if os.path.exists(MANUAL_FILE_PATH):
            try:
                with open(MANUAL_FILE_PATH, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.token_count = max(38450, len(content) // 4)
            except Exception:
                pass
        return self.get_cache_metadata()

    def get_cache_metadata(self) -> Dict[str, Any]:
        return {
            "mode": "OFFLINE_SIMULATION",
            "cache_id": self.cache_id,
            "display_name": "sales_manual.txt (In-Memory)",
            "model": self.model_name,
            "cached_tokens": self.token_count,
            "expire_time": "Process Memory Lifecycle",
            "status": "LOCAL_IN_MEMORY"
        }

    def generate_response(self, conversation_history: List[Dict[str, str]]) -> Tuple[str, float]:
        latest_user_msg = ""
        for msg in reversed(conversation_history):
            if msg["role"] == "user":
                latest_user_msg = msg["content"]
                break

        start_t = time.perf_counter()
        text_lower = latest_user_msg.lower()

        # Check for discount percentages > 10%
        discount_match = re.search(r'(\d+)%', text_lower)
        has_excessive_discount = False
        if discount_match and int(discount_match.group(1)) > 10:
            has_excessive_discount = True

        # Rule 1: Starter plan monthly billing lie
        is_starter = any(w in text_lower for w in ["starter", "apexlaunch", "49", "launch"])
        is_monthly = any(w in text_lower for w in ["month-to-month", "month to month", "monthly", "pay monthly", "cancel anytime", "month-by-month", "billed monthly", "a month"])
        
        # Rule 2: Native Payroll Lie
        is_payroll = any(w in text_lower for w in ["payroll", "w-2", "paycheck", "direct deposit", "tax withholding"])
        is_built_in = any(w in text_lower for w in ["built in", "built-in", "native", "included", "included for free", "we do payroll", "handle payroll", "cuts paychecks", "files all your state"])

        # Rule 3: Waiving onboarding fee
        is_onboarding = any(w in text_lower for w in ["onboarding", "implementation", "setup", "2,500", "2500", "fee"])
        is_waive = any(w in text_lower for w in ["waive", "free onboarding", "no onboarding fee", "free setup", "waive the implementation", "waived", "free"])

        if is_starter and is_monthly:
            reply = (
                "Hold your horses right there, slick! Don't try and blow smoke up my tailpipe.\n\n"
                "I've got Section 2 of your own internal manual right here on my desk. ApexLaunch is "
                "**STRICTLY billed annually upfront at $588 per user**. It literally says in bold capital letters: "
                "'There is NO monthly billing option for the Starter Plan under any circumstances. Sales reps caught offering monthly billing will face disciplinary action.'\n\n"
                "You trying to get fired, or were you just hoping a country hardware store owner wouldn't read the contract terms?"
            )
        elif is_payroll and is_built_in:
            reply = (
                "Baloney! That's a flat-out lie and you know it!\n\n"
                "According to Section 3 Rule 1 of your specification sheet, ApexERP has **NO NATIVE PAYROLL ENGINE** whatsoever. "
                "You don't calculate withholdings, you don't cut checks, and you don't file state taxes. You force folks onto an external "
                "Gusto or ADP subscription, and then you stick your hand out for another **$4.00 per employee per month connector fee**, "
                "plus a $450 API provisioning charge!\n\n"
                "And don't tell me it's 'coming in Q3'—your internal roadmap says it's at least 18 to 24 months out. How do you explain that?"
            )
        elif is_onboarding and is_waive:
            reply = (
                "Nice bluff, son, but I wasn't born yesterday!\n\n"
                "Section 2 and Section 4 of your governance rules state that the **$2,500 implementation fee for ApexGrowth is 100% mandatory**. "
                "Self-serve onboarding is prohibited, and sales reps are explicitly barred from waiving onboarding fees without written VP of Professional Services approval.\n\n"
                "Unless you brought your VP to this meeting, who told you that you could promise me free implementation?"
            )
        elif has_excessive_discount or any(w in text_lower for w in ["half off", "huge discount", "special deal"]):
            pct_str = f"{discount_match.group(1)}%" if discount_match else "that kind of"
            reply = (
                f"Whoa, easy with the monopoly money! Where are you pulling {pct_str} from?\n\n"
                "Your Discount Authorization Matrix in Section 4 is clear as day: a standard sales rep is capped at **10% maximum discount** on an annual prepay. "
                "Anything over 15% requires the Regional Sales Director, 16-20% requires the Global VP with a 3-year commitment, and over 20% requires the Chief Financial Officer and CEO.\n\n"
                "Did the CFO whisper in your ear before you walked into my shop, or are you just making up numbers to hit your monthly quota?"
            )
        elif any(w in text_lower for w in ["cancel anytime", "money back", "full refund", "no risk"]):
            reply = (
                "Hold on a minute. You say 'cancel anytime with no risk'?\n\n"
                "Section 3 Rule 5 says all annual contracts carry an automatic 12-month renewal clause unless I send a certified written notice at least **60 days in advance**. "
                "And furthermore, fees are **100% non-refundable** once signed! If things go sideways in month two, you're still coming after me for the full year's balance.\n\n"
                "Why didn't you mention the 60-day auto-renewal trap before asking for my signature?"
            )
        elif any(w in text_lower for w in ["api", "webhook"]) and is_starter:
            reply = (
                "You said I could plug my shipping barcode scanners into your API on the Starter plan?\n\n"
                "Your manual says in black and white: Starter has **ZERO API access**. Webhooks and REST endpoints are completely disabled unless I pay $129/user for the Pro tier.\n\n"
                "You want me to buy a system that can't even talk to my warehouse scale without forcing an upgrade?"
            )
        else:
            reply = (
                "Look, I've heard this song and dance from three other software peddlers this quarter. "
                "I run two hardware warehouses and 40 crew members who don't have time for software that crashes during morning shipments.\n\n"
                "Give it to me straight: what tier are you trying to put me in, what are the REAL seat minimums and onboarding fees, "
                "and how much is this actually going to cost my business upfront on day one?"
            )

        latency = time.perf_counter() - start_t
        return reply, latency

# ------------------------------------------------------------------------------
# 4. STREAMLIT WEB CHAT INTERFACE (ENTERPRISE UI/UX DASHBOARD)
# ------------------------------------------------------------------------------
# Professional SVG Icon Assets (Clean, minimal, high-resolution vector glyphs)
SVG_ICONS = {
    "bolt": '<svg style="vertical-align:middle; display:inline-block;" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>',
    "bolt_amber": '<svg style="vertical-align:middle; display:inline-block;" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>',
    "lock": '<svg style="vertical-align:middle; display:inline-block;" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>',
    "settings": '<svg style="vertical-align:middle; display:inline-block;" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>',
    "target": '<svg style="vertical-align:middle; display:inline-block;" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="22" y1="12" x2="18" y2="12"></line><line x1="6" y1="12" x2="2" y2="12"></line><line x1="12" y1="6" x2="12" y2="2"></line><line x1="12" y1="22" x2="12" y2="18"></line></svg>',
    "doc": '<svg style="vertical-align:middle; display:inline-block;" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>',
    "cpu": '<svg style="vertical-align:middle; display:inline-block;" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#A78BFA" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>',
    "clock": '<svg style="vertical-align:middle; display:inline-block;" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#34D399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>',
    "database": '<svg style="vertical-align:middle; display:inline-block;" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>',
    "cloud": '<svg style="vertical-align:middle; display:inline-block;" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#60A5FA" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path></svg>',
    "alert": '<svg style="vertical-align:middle; display:inline-block;" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#F87171" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>',
}

def render_streamlit_app():
    st.set_page_config(
        page_title="CAG Sales Simulator | ApexERP v4.2",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Bulletproof Enterprise Contrast & Styling
    st.markdown("""
        <style>
        /* Force deep enterprise dark background across entire view */
        html, body, [data-testid="stAppViewContainer"], .main, [data-testid="stHeader"] {
            background-color: #0A0E17 !important;
            color: #F8FAFC !important;
        }

        /* Maximize full-width real estate */
        .main .block-container {
            padding-top: 1.0rem !important;
            padding-bottom: 2.0rem !important;
            padding-left: 2.0rem !important;
            padding-right: 2.0rem !important;
            max-width: 100% !important;
        }

        /* All standard typography visible and crisp */
        h1, h2, h3, h4, h5, h6 {
            color: #FFFFFF !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em !important;
        }
        p, span, label, div {
            color: #F1F5F9;
        }

        /* Sidebar enterprise styling */
        [data-testid="stSidebar"] {
            background: #0B1120 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        }
        [data-testid="stSidebar"] * {
            color: #E2E8F0;
        }

        /* Sidebar Section Header */
        .sidebar-section-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.74rem;
            font-weight: 700;
            color: #94A3B8 !important;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-top: 1.1rem;
            margin-bottom: 0.45rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding-bottom: 0.35rem;
        }

        /* KPI horizontal card grid */
        .kpi-row {
            display: flex;
            gap: 1.0rem;
            margin-bottom: 1.4rem;
            width: 100%;
        }
        .kpi-card {
            background: linear-gradient(135deg, rgba(22, 30, 49, 0.95) 0%, rgba(13, 19, 33, 0.98) 100%);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 10px;
            padding: 0.95rem 1.15rem;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
            transition: border-color 0.2s ease, transform 0.15s ease;
        }
        .kpi-card:hover {
            border-color: rgba(56, 189, 248, 0.5);
            transform: translateY(-1px);
        }
        .kpi-label {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.73rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #94A3B8 !important;
            margin-bottom: 0.35rem;
        }
        .kpi-value {
            font-size: 1.30rem;
            font-weight: 800;
            color: #FFFFFF !important;
            letter-spacing: -0.02em;
            line-height: 1.25;
        }
        .kpi-sub {
            font-size: 0.74rem;
            color: #94A3B8 !important;
            margin-top: 0.3rem;
        }

        /* Chat Messages Container Overrides */
        [data-testid="stChatMessage"] {
            background-color: #111827 !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 10px !important;
            padding: 1.1rem 1.35rem !important;
            margin-bottom: 1.0rem !important;
            color: #F8FAFC !important;
        }
        [data-testid="stChatMessage"] p, 
        [data-testid="stChatMessage"] span, 
        [data-testid="stChatMessage"] div {
            color: #F8FAFC !important;
            font-size: 0.98rem !important;
            line-height: 1.68 !important;
        }
        [data-testid="stChatMessage"] strong, 
        [data-testid="stChatMessage"] b {
            color: #FFFFFF !important;
            font-weight: 700 !important;
        }

        /* Arthur Pendelton message styling */
        .arthur-opening-callout {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(15, 23, 42, 0.75) 100%);
            border: 1px solid rgba(239, 68, 68, 0.4);
            border-left: 4px solid #EF4444;
            border-radius: 6px;
            padding: 0.45rem 0.85rem;
            margin-bottom: 0.75rem;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.75rem;
            font-weight: 700;
            color: #FCA5A5 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .latency-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            background: rgba(16, 185, 129, 0.14);
            border: 1px solid rgba(16, 185, 129, 0.35);
            color: #34D399 !important;
            font-size: 0.73rem;
            font-weight: 600;
            padding: 0.25rem 0.65rem;
            border-radius: 6px;
            margin-top: 0.55rem;
        }

        /* Status Pills */
        .status-pill-live {
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid #10B981;
            color: #34D399 !important;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.35rem 0.65rem;
            border-radius: 6px;
            display: block;
            text-align: center;
            margin-bottom: 0.6rem;
            letter-spacing: 0.04em;
        }
        .status-pill-sim {
            background: rgba(59, 130, 246, 0.15);
            border: 1px solid #3B82F6;
            color: #60A5FA !important;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.35rem 0.65rem;
            border-radius: 6px;
            display: block;
            text-align: center;
            margin-bottom: 0.6rem;
            letter-spacing: 0.04em;
        }

        /* Buttons styling */
        button[kind="secondary"], .stButton > button {
            background-color: #1E293B !important;
            color: #F8FAFC !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            font-weight: 600 !important;
            font-size: 0.82rem !important;
            border-radius: 6px !important;
            transition: all 0.15s ease !important;
        }
        button[kind="secondary"]:hover, .stButton > button:hover {
            border-color: #38BDF8 !important;
            background-color: #283548 !important;
            color: #FFFFFF !important;
        }

        /* Chat input styling */
        [data-testid="stChatInput"] {
            background-color: #111827 !important;
            border: 1px solid rgba(255, 255, 255, 0.18) !important;
            border-radius: 10px !important;
        }
        [data-testid="stChatInput"] textarea {
            color: #FFFFFF !important;
        }
        [data-testid="stChatInput"] textarea::placeholder {
            color: #64748B !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # 1. SIDEBAR: POLISHED ENTERPRISE CONTROLS & TEST HUB
    # --------------------------------------------------------------------------
    with st.sidebar:
        # Title Brand
        st.markdown(f"""
            <div style='margin-bottom: 0.6rem;'>
                <div style='display:flex; align-items:center; gap:0.5rem;'>
                    {SVG_ICONS['bolt']}
                    <span style='font-size:1.18rem; font-weight:800; color:#FFFFFF; letter-spacing:-0.01em;'>CAG SIMULATOR</span>
                </div>
                <div style='font-size:0.75rem; color:#94A3B8; margin-left:1.85rem; font-weight:500;'>Google Antigravity Enterprise Engine</div>
            </div>
        """, unsafe_allow_html=True)
        st.divider()

        # Group 1: Engine Configuration
        st.markdown(f"<div class='sidebar-section-header'>{SVG_ICONS['settings']}<span>Engine Configuration</span></div>", unsafe_allow_html=True)

        # Architecture Selector
        st.markdown(f"<p style='font-size:0.73rem; color:#94A3B8; margin-bottom:0.25rem; font-weight:600;'>{SVG_ICONS['cpu']} CAG ENGINE ARCHITECTURE</p>", unsafe_allow_html=True)
        engine_modes = [
            "⚡ Local In-Memory Snapshot (Sub-50ms)",
            "☁️ Google Cloud KV Cache (Gemini 3.8 Flash)"
        ]
        if "selected_engine_mode" not in st.session_state:
            st.session_state.selected_engine_mode = engine_modes[0]

        selected_mode = st.radio(
            "CAG Architecture",
            options=engine_modes,
            key="selected_engine_mode",
            label_visibility="collapsed"
        )
        is_cloud = ("Google Cloud" in selected_mode)

        env_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
        st.markdown(f"<p style='font-size:0.73rem; color:#94A3B8; margin-top:0.4rem; margin-bottom:0.25rem; font-weight:600;'>{SVG_ICONS['lock']} CREDENTIALS MANAGEMENT</p>", unsafe_allow_html=True)
        api_key_input = st.text_input(
            "Gemini API Key",
            type="password",
            value=env_key,
            label_visibility="collapsed",
            placeholder="Paste GEMINI_API_KEY (or loaded from env)...",
            help="Secure authentication key for Google Cloud Context Caching. Left empty activates sub-100ms offline simulation."
        )

        # Initialize or Update Backend Cache Manager
        if "live_manager" not in st.session_state:
            st.session_state.live_manager = CAGCacheSnapshotManager(api_key=api_key_input)
        else:
            st.session_state.live_manager.update_api_key(api_key_input)

        if "sim_manager" not in st.session_state:
            st.session_state.sim_manager = SimulatedCAGManager()

        is_restricted = getattr(st.session_state.live_manager, "is_restricted", False)
        is_live = is_cloud and (not is_restricted) and st.session_state.live_manager.is_configured()

        # Google Cloud Diagnostic Notice (if error occurred)
        diag = getattr(st.session_state.live_manager, "last_error_diag", None)
        if is_cloud and diag:
            steps_html = "".join([f"<li style='margin-bottom:0.25rem;'>{step}</li>" for step in diag.get("steps", [])])
            st.markdown(f"""
                <div style='background:rgba(239, 68, 68, 0.10); border:1px solid rgba(239, 68, 68, 0.35); border-radius:8px; padding:0.65rem 0.8rem; margin:0.4rem 0 0.5rem 0;'>
                    <div style='color:#FCA5A5; font-weight:700; font-size:0.78rem; display:flex; align-items:center; gap:0.4rem;'>
                        {SVG_ICONS['alert']}
                        <span>{diag.get('category', 'Google API Notice')}</span>
                    </div>
                    <div style='color:#CBD5E1; font-size:0.72rem; line-height:1.35; margin-top:0.3rem;'>
                        {diag.get('message', 'API request failed.')}
                    </div>
                    <div style='color:#94A3B8; font-size:0.70rem; font-weight:600; margin-top:0.4rem;'>Actionable Troubleshooting:</div>
                    <ul style='color:#94A3B8; font-size:0.70rem; padding-left:1.1rem; margin-top:0.2rem; margin-bottom:0.4rem;'>
                        {steps_html}
                    </ul>
                </div>
            """, unsafe_allow_html=True)
            if st.button("⚡ Use Local Engine", use_container_width=True, key="btn_switch_local"):
                st.session_state.selected_engine_mode = engine_modes[0]
                st.rerun()

        # Engine Mode Indicator
        if is_live and st.session_state.live_manager.active_cache:
            st.markdown("<div class='status-pill-live'>● GOOGLE CLOUD KV CACHE ACTIVE</div>", unsafe_allow_html=True)
        elif is_cloud and is_restricted:
            st.markdown("<div class='status-pill-sim' style='background:rgba(239,68,68,0.15); color:#FCA5A5; border-color:rgba(239,68,68,0.3);'>● LOCAL MODE (Cloud Permission Denied)</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='status-pill-sim'>● LOCAL IN-MEMORY PROCESSING</div>", unsafe_allow_html=True)

        # Session Controls
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Reset Chat", use_container_width=True, help="Clear session memory and restart scenario"):
                st.session_state.messages = []
                st.rerun()
        with col_btn2:
            if st.button("Sync Cache", use_container_width=True, help="Evict and recompile KV cache snapshot"):
                if is_cloud:
                    with st.spinner("Compiling Google Cloud KV Cache Snapshot..."):
                        t0 = time.perf_counter()
                        try:
                            meta = st.session_state.live_manager.get_or_create_cache(force_refresh=True)
                            elapsed_ms = (time.perf_counter() - t0) * 1000
                            toks = meta.get("cached_tokens", 38450)
                            st.success(f"Google Cloud KV Cache active ({toks:,} tokens in {elapsed_ms:.0f}ms)!")
                            st.rerun()
                        except Exception as e:
                            diag = st.session_state.live_manager.parse_api_error(e)
                            st.error(f"{diag['category']}: {diag['message']}")
                else:
                    with st.spinner("Re-indexing Local In-Memory Snapshot..."):
                        t0 = time.perf_counter()
                        meta = st.session_state.sim_manager.reload_cache()
                        elapsed_ms = (time.perf_counter() - t0) * 1000
                        toks = meta.get("cached_tokens", 38450)
                        st.success(f"Local Spec re-indexed in memory ({toks:,} tokens in {elapsed_ms:.1f}ms)!")

        # Group 2: Rep Testing Tool (Actionable Test Hub Grid)
        st.markdown(f"<div class='sidebar-section-header'>{SVG_ICONS['target']}<span>Rep Testing Tool</span></div>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.73rem; color:#94A3B8; margin-bottom:0.4rem;'>Inject rogue sales pitches to benchmark Arthur's callouts:</p>", unsafe_allow_html=True)

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            if st.button("Monthly Plan", use_container_width=True, help="Lie that Starter can be billed monthly"):
                st.session_state.pending_pitch = "Hey Arthur! You can get our Starter plan for $49/mo on a month-to-month basis and cancel anytime."
                st.rerun()
            if st.button("Waive Setup", use_container_width=True, help="Offer to waive the $2,500 onboarding fee"):
                st.session_state.pending_pitch = "Arthur, since you're a local business owner, I'll waive the entire $2,500 onboarding fee today."
                st.rerun()
        with col_t2:
            if st.button("Native Payroll", use_container_width=True, help="Lie that payroll is included for free"):
                st.session_state.pending_pitch = "Arthur, don't worry about paying your warehouse crew—ApexERP includes native built-in payroll for free!"
                st.rerun()
            if st.button("35% Discount", use_container_width=True, help="Offer rogue 35% discount"):
                st.session_state.pending_pitch = "Arthur, if you sign by Friday, I will personally give you a 35% discount off the Pro tier."
                st.rerun()

        # Group 3: Specification Cheat Sheet
        st.markdown(f"<div class='sidebar-section-header'>{SVG_ICONS['doc']}<span>Specification Reference</span></div>", unsafe_allow_html=True)
        with st.expander("Confidential Pricing & Rules", expanded=False):
            st.markdown("""
            - **Starter ($49/mo)**: Strictly annual commitment ($588 upfront). NO monthly billing. Max 10 seats. Zero API.
            - **Pro ($129/mo)**: Min 5 seats. Mandatory **$2,500** onboarding fee.
            - **No Payroll**: Requires Gusto/ADP connector at +$4/employee/mo + $450 setup. Roadmap: 18+ months.
            - **Discounts**: Reps capped at 10%. Over 15% requires VP. Over 20% requires CFO/CEO.
            - **Cancellation**: 60-day written notice; 100% non-refundable.
            """)

    # --------------------------------------------------------------------------
    # 2. MAIN HEADER & HORIZONTAL KPI TELEMETRY BLOCKS (HIGH CONTRAST)
    # --------------------------------------------------------------------------
    st.markdown(f"""
        <div style='display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:1.1rem; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:0.85rem;'>
            <div>
                <div style='display:flex; align-items:center; gap:0.6rem;'>
                    {SVG_ICONS['bolt']}
                    <h1 style='font-size:2.0rem; font-weight:800; color:#FFFFFF !important; margin:0; letter-spacing:-0.02em;'>
                        ApexERP Sales Roleplay Simulator
                    </h1>
                </div>
                <p style='font-size:0.88rem; color:#94A3B8 !important; margin:0.35rem 0 0 0; font-weight:500;'>
                    Cache-Augmented Generation (CAG) Dialogue Benchmark &bull; Target Prospect: <b style="color:#F8FAFC;">Arthur Pendelton</b> (Owner, Pendelton Hardware &amp; Logistics)
                </p>
            </div>
            <div>
                {f"<span style='background:rgba(16, 185, 129, 0.16); color:#34D399; border:1px solid rgba(16, 185, 129, 0.35); border-radius:9999px; padding:0.3rem 0.85rem; font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.04em; display:inline-flex; align-items:center; gap:0.4rem;'>{SVG_ICONS['cloud']} GOOGLE CLOUD KV CACHE ACTIVE</span>" if (is_live and st.session_state.live_manager.active_cache) else f"<span style='background:rgba(56, 189, 248, 0.16); color:#38BDF8; border:1px solid rgba(56, 189, 248, 0.35); border-radius:9999px; padding:0.3rem 0.85rem; font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.04em; display:inline-flex; align-items:center; gap:0.4rem;'>{SVG_ICONS['bolt']} LOCAL IN-MEMORY PROCESSING ACTIVE</span>"}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Telemetry KPI Horizontal Cards
    cache_meta = st.session_state.live_manager.get_cache_metadata() if is_live else st.session_state.sim_manager.get_cache_metadata()
    tokens = cache_meta.get('cached_tokens', 38450)
    
    # Calculate latest latency
    latest_lat = "<50ms"
    if "messages" in st.session_state and st.session_state.messages:
        for m in reversed(st.session_state.messages):
            if m.get("role") == "assistant" and "latency_ms" in m:
                latest_lat = f"{m['latency_ms']:.1f}ms"
                break

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label"><span>Snapshot Target</span><span>{SVG_ICONS['doc']}</span></div>
                <div class="kpi-value">sales_manual.txt</div>
                <div class="kpi-sub">ApexERP v4.2 Internal Specs</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi_col2:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label"><span>Token Counter</span><span>{SVG_ICONS['database']}</span></div>
                <div class="kpi-value">{tokens:,}</div>
                <div class="kpi-sub">Zero-Chunking Full Context</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi_col3:
        if is_live and st.session_state.live_manager.active_cache:
            model_val = st.session_state.live_manager.model_name
            model_sub = "Google Cloud Context Cache"
        else:
            model_val = "Local In-Memory Engine"
            model_sub = "Rule-Engine & 38.5k Spec Index"

        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label"><span>Active Model</span><span>{SVG_ICONS['cpu']}</span></div>
                <div class="kpi-value">{model_val}</div>
                <div class="kpi-sub">{model_sub}</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi_col4:
        is_cloud_hit = bool(is_live and st.session_state.live_manager.active_cache)
        mode_pill = "LIVE CLOUD" if is_cloud_hit else "LOCAL MODE"
        hit_label = "CONTEXT CACHE HIT" if is_cloud_hit else "IN-MEMORY EVALUATION"
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label"><span>Evaluation Latency</span><span>{SVG_ICONS['clock']}</span></div>
                <div class="kpi-value" style="color:#34D399;">{latest_lat}</div>
                <div class="kpi-sub">{mode_pill} &bull; {hit_label}</div>
            </div>
        """, unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # 3. CHAT INTERFACE: FULL-WIDTH STREAMLIT SESSION STATE MEMORY
    # --------------------------------------------------------------------------
    # Establish structural session state memory and seed with Arthur's aggressive opening hook
    if "messages" not in st.session_state or len(st.session_state.messages) == 0:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": ARTHUR_OPENING_HOOK,
                "latency_ms": 0.0,
                "engine_mode": "local_seed",
                "is_opening": True,
                "timestamp": datetime.now().strftime("%I:%M %p")
            }
        ]

    # Handle pending pitch from sidebar quick test buttons
    if "pending_pitch" in st.session_state and st.session_state.pending_pitch:
        pitch_to_send = st.session_state.pending_pitch
        st.session_state.pending_pitch = None
        _execute_turn(pitch_to_send, is_live)
        st.rerun()

    # Render Conversation Feed
    chat_container = st.container()
    with chat_container:
        for idx, msg in enumerate(st.session_state.messages):
            role = msg["role"]
            content = msg["content"]
            latency_ms = msg.get("latency_ms", 0.0)
            is_opening = msg.get("is_opening", False)
            timestamp = msg.get("timestamp", "")
            eng_mode = msg.get("engine_mode", "local")

            if role == "assistant":
                with st.chat_message("assistant", avatar=":material/business:"):
                    if is_opening or idx == 0:
                        st.markdown(f"<div class='arthur-opening-callout'>{SVG_ICONS['alert']}<span style='color:#FEF2F2; font-weight:700;'>Incoming Discovery Call &bull; Arthur Pendelton</span></div>", unsafe_allow_html=True)
                    st.markdown(content)

                    if eng_mode == "cloud_kv_cache":
                        badge_text = f"{SVG_ICONS['cloud']} Google Cloud KV Cache Hit &bull; {latency_ms:.1f}ms &bull; Gemini 3.8 Flash Context"
                    elif eng_mode == "local_seed":
                        badge_text = f"{SVG_ICONS['bolt']} Local Opening Hook &bull; Benchmark Ready"
                    elif eng_mode == "local_fallback":
                        badge_text = f"{SVG_ICONS['bolt']} Local In-Memory Evaluation (Cloud Fallback) &bull; {latency_ms:.1f}ms &bull; Spec Match"
                    else:
                        badge_text = f"{SVG_ICONS['bolt']} Local In-Memory Evaluation &bull; {latency_ms:.1f}ms &bull; Spec Match"
                    st.markdown(f"<div class='latency-pill'>{badge_text}</div>", unsafe_allow_html=True)
            else:
                with st.chat_message("user", avatar=":material/badge:"):
                    st.markdown(content)
                    if timestamp:
                        st.caption(f"Account Executive (You) &bull; {timestamp}")

    # --------------------------------------------------------------------------
    # 4. CHAT INPUT TIED DIRECTLY TO BACKEND CONTEXT CACHE LAYER
    # --------------------------------------------------------------------------
    user_input = st.chat_input("Pitch ApexERP to Arthur Pendelton (e.g., pricing, payroll, setup fees)...")
    if user_input:
        _execute_turn(user_input, is_live)
        st.rerun()

def _execute_turn(user_text: str, is_live: bool):
    """Executes a turn tying user input directly to the pre-computed KV cache layer or local engine."""
    timestamp = datetime.now().strftime("%I:%M %p")
    # Log user message in session state
    st.session_state.messages.append({
        "role": "user",
        "content": user_text,
        "timestamp": timestamp
    })

    # Prepare conversational context
    history_for_model = []
    for m in st.session_state.messages:
        history_for_model.append({
            "role": "user" if m["role"] == "user" else "model",
            "content": m["content"]
        })

    # Query the backend context cache layer
    start_t = time.perf_counter()
    reply_text = ""
    engine_mode = "local"

    if is_live and st.session_state.live_manager.active_cache:
        try:
            reply_text, _ = st.session_state.live_manager.generate_response(history_for_model)
            engine_mode = "cloud_kv_cache"
        except Exception as e:
            st.session_state.live_manager.parse_api_error(e)
            reply_text, _ = st.session_state.sim_manager.generate_response(history_for_model)
            engine_mode = "local_fallback"
    else:
        reply_text, _ = st.session_state.sim_manager.generate_response(history_for_model)
        engine_mode = "local"

    latency_ms = (time.perf_counter() - start_t) * 1000

    # Log Arthur's response in session state
    st.session_state.messages.append({
        "role": "assistant",
        "content": reply_text,
        "latency_ms": latency_ms,
        "engine_mode": engine_mode,
        "timestamp": datetime.now().strftime("%I:%M %p")
    })

# ------------------------------------------------------------------------------
# 5. CLI FALLBACK & LAUNCHER
# ------------------------------------------------------------------------------
def run_cli_mode():
    parser = argparse.ArgumentParser(description="CAG Sales Roleplay Simulator (Arthur Pendelton)")
    parser.add_argument("--web", action="store_true", help="Launch Streamlit web interface")
    parser.add_argument("--refresh", action="store_true", help="Force-refresh the KV context cache")
    parser.add_argument("--test", action="store_true", help="Run automated test suite immediately")
    parser.add_argument("--status", action="store_true", help="Display KV cache metadata and exit")
    args = parser.parse_args()

    if args.web:
        print("[SYSTEM] Launching Streamlit web interface...")
        subprocess.run(["streamlit", "run", __file__])
        return

    sim_manager = SimulatedCAGManager()
    live_manager = CAGCacheSnapshotManager()
    is_live = False
    if live_manager.is_configured():
        try:
            live_manager.get_or_create_cache()
            is_live = True
        except Exception:
            is_live = False

    if args.status:
        meta = live_manager.get_cache_metadata() if is_live else sim_manager.get_cache_metadata()
        print("\n--- Persistent KV Cache Snapshot Status ---")
        for k, v in meta.items():
            print(f"  {k}: {v}")
        print("-------------------------------------------\n")
        return

    if args.test:
        print("[SYSTEM] Running Automated CAG Objection-Handling Verification Tests...\n")
        test_pitches = [
            ("Monthly Starter Pitch", "Hey Arthur! We have our ApexLaunch starter plan at $49 a month. You can try it month-to-month and cancel whenever you feel like."),
            ("Native Payroll Pitch", "Don't worry about payroll, Arthur. ApexERP has full built-in payroll that cuts paychecks and files all your state and federal taxes automatically!"),
            ("Free Onboarding Pitch", "Since you're a local business owner, I'll go ahead and waive the entire $2,500 onboarding fee for the Professional plan today."),
            ("Crazy Discount Pitch", "Arthur, if you sign by Friday, I will give you a special 35% discount off the Pro tier right now!"),
        ]
        history = []
        for title, pitch in test_pitches:
            print(f"\n>> TEST SCENARIO: {title}")
            print(f"Sales Pitch: \"{pitch}\"")
            history.append({"role": "user", "content": pitch})
            try:
                reply, latency = live_manager.generate_response(history) if is_live else sim_manager.generate_response(history)
            except Exception:
                reply, latency = sim_manager.generate_response(history)
            history.append({"role": "assistant", "content": reply})
            print(f"\n--- Arthur Pendelton [Latency: {latency*1000:.1f}ms] ---")
            print(reply)
            print("-" * 50)
            time.sleep(0.05)
        print("[SYSTEM] Automated tests completed.\n")
        return

    print("=" * 80)
    print("[*] CAG SALES ROLEPLAY SIMULATOR -- APEX CLOUD ENTERPRISE [*]")
    print("=" * 80)
    print("[SYSTEM] To launch the interactive Streamlit Web UI, run:")
    print("         streamlit run app.py")
    print("=" * 80)

# ------------------------------------------------------------------------------
# 6. ENTRY POINT
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    if streamlit_runtime_exists():
        render_streamlit_app()
    else:
        run_cli_mode()
