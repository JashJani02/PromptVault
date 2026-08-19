import streamlit as st
import urllib.request
from db import add_entry, update_entry, get_entries, delete_entry, FIELDS, PROVIDERS

LINK_KEYS = ("image_url", "video_url", "chat_link", "artifact_link")


@st.cache_data(ttl=300, show_spinner=False)
def _is_loadable_image(url):
    """Checks whether a URL actually resolves to an image before we try
    to render it with st.image(), so broken links show as plain text
    instead of a broken-image placeholder. Cached for 5 minutes so we're
    not re-checking the same URL on every rerun."""
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            content_type = resp.headers.get("Content-Type", "")
            return content_type.lower().startswith("image/")
    except Exception:
        return False


def _provider_inputs(prefix, entry=None):
    """Renders the Provider selectbox, OUTSIDE any st.form so it stays
    reactive (widgets inside st.form only update on submit, not per
    interaction). The custom text field only appears when 'Other' or
    'Local / Self-hosted' is selected, and this reacts immediately since
    the selectbox lives outside the form. Values are read back out of
    st.session_state at submit time using the same prefix."""
    options = ["None"] + PROVIDERS

    default_choice = "None"
    default_custom = ""
    if entry and entry["provider"]:
        current = entry["provider"]
        if current in PROVIDERS:
            default_choice = current
        else:
            default_choice = "Other"
            default_custom = current

    choice_key = f"{prefix}_provider_choice"
    custom_key = f"{prefix}_custom_provider"

    col1, col2 = st.columns(2)
    with col1:
        choice = st.selectbox(
            "Provider (optional)",
            options,
            index=options.index(default_choice),
            key=choice_key,
        )
    with col2:
        if choice in ("Other", "Local / Self-hosted"):
            st.text_input(
                "Model / harness name",
                value=default_custom,
                placeholder="e.g. Llama 3 via Ollama, custom agent, etc.",
                key=custom_key,
            )
    


def _resolve_provider(prefix):
    """Reads the provider choice + custom text back from session_state."""
    choice = st.session_state.get(f"{prefix}_provider_choice", "None")
    custom = st.session_state.get(f"{prefix}_custom_provider", "")
    if choice == "None":
        return None
    if choice in ("Other", "Local / Self-hosted") and custom.strip():
        return custom.strip()
    return choice


def _entry_title(entry):
    """Used as the expander title. Falls back to a snippet of the first
    filled field if no topic was given, so entries are never unlabeled."""
    if entry["topic"]:
        return entry["topic"]
    for key, _ in FIELDS:
        value = entry[key]
        if value:
            snippet = value.strip().replace("\n", " ")
            if len(snippet) > 60:
                snippet = snippet[:60] + "..."
            return snippet
    return "(untitled entry)"


def render():
    st.title("🗂️ Storage")
    st.caption("Save and revisit your AI conversations: prompts, responses, media links, and more, all in one place.")
    user_id = st.session_state.user_id

    # ---------- Add Entry ----------
    with st.expander("➕ Add Entry", expanded=True):
        st.caption("Fill in whichever fields apply. Leave the rest blank.")

        _provider_inputs("add")

        with st.form("add_entry_form", clear_on_submit=True):
            topic = st.text_input("Chat Headline / Topic (optional)", placeholder="e.g. Refactor auth module")

            values = {}
            values["prompt"] = st.text_area("Prompt", placeholder="None", height=80)
            values["response"] = st.text_area("Response", placeholder="None", height=80)

            col1, col2 = st.columns(2)
            with col1:
                values["image_url"] = st.text_input("Image URL", placeholder="None")
                values["chat_link"] = st.text_input("Chat Link", placeholder="None")
            with col2:
                values["video_url"] = st.text_input("Video URL", placeholder="None")
                values["artifact_link"] = st.text_input("Artifact Link", placeholder="None")

            category = st.text_input("Tags (optional)", placeholder="e.g. coding, python, refactor:  comma separated, auto-lowercased")

            submitted = st.form_submit_button("Save Entry", use_container_width=True)

            if submitted:
                has_content = any(v.strip() for v in values.values() if v)
                if not has_content:
                    st.error("Fill in at least one field before saving.")
                else:
                    provider = _resolve_provider("add")
                    add_entry(user_id, values, category or None, provider, topic or None)
                    st.success("✅ Saved!")
                    st.rerun()

    st.divider()

    # ---------- Search ----------
    entries = get_entries(user_id)

    if not entries:
        st.info("No entries yet. Add one above!")
        return

    search_query = st.text_input(
        "🔎 Search",
        placeholder="Search topic, prompts, responses, links, category, or provider...",
    )

    if search_query.strip():
        q = search_query.strip().lower()
        content_keys = [key for key, _ in FIELDS] + ["topic", "provider"]

        def matches(entry):
            # Match against content fields directly
            if any(entry[key] and q in entry[key].lower() for key in content_keys):
                return True
            # Match against individual tags (split on comma)
            if entry["category"]:
                tags = [t.strip() for t in entry["category"].split(",") if t.strip()]
                if any(q in tag for tag in tags):
                    return True
            return False

        entries = [e for e in entries if matches(e)]

    st.caption(f"{len(entries)} entries")

    if not entries:
        st.info("No entries match your search.")
        return

    # ---------- View / Edit Entries ----------
    editing_id = st.session_state.get("editing_entry_id")

    for entry in entries:
        is_editing = editing_id == entry["id"]

        with st.expander(_entry_title(entry), expanded=is_editing):
            with st.container():
                if is_editing:
                    prefix = f"edit_{entry['id']}"

                    _provider_inputs(prefix, entry=entry)

                    with st.form(f"{prefix}_form"):
                        topic = st.text_input(
                            "Chat Headline / Topic (optional)", value=entry["topic"] or ""
                        )

                        values = {}
                        values["prompt"] = st.text_area("Prompt", value=entry["prompt"] or "", height=80)
                        values["response"] = st.text_area("Response", value=entry["response"] or "", height=80)

                        col1, col2 = st.columns(2)
                        with col1:
                            values["image_url"] = st.text_input("Image URL", value=entry["image_url"] or "")
                            values["chat_link"] = st.text_input("Chat Link", value=entry["chat_link"] or "")
                        with col2:
                            values["video_url"] = st.text_input("Video URL", value=entry["video_url"] or "")
                            values["artifact_link"] = st.text_input("Artifact Link", value=entry["artifact_link"] or "")

                        category = st.text_input("Tags (optional)", value=entry["category"] or "", placeholder="e.g. coding, python, refactor:  comma separated")

                        col1, col2 = st.columns(2)
                        with col1:
                            save_clicked = st.form_submit_button("Save Changes", use_container_width=True)
                        with col2:
                            cancel_clicked = st.form_submit_button("Cancel", use_container_width=True)

                        if save_clicked:
                            has_content = any(v.strip() for v in values.values() if v)
                            if not has_content:
                                st.error("Fill in at least one field before saving.")
                            else:
                                provider = _resolve_provider(prefix)
                                update_entry(entry["id"], user_id, values, category or None, provider, topic or None)
                                st.session_state.editing_entry_id = None
                                st.success("✅ Updated!")
                                st.rerun()

                        if cancel_clicked:
                            st.session_state.editing_entry_id = None
                            st.rerun()

                else:
                    for key, label in FIELDS:
                        value = entry[key]
                        if not value:
                            continue

                        if key == "image_url":
                            if _is_loadable_image(value):
                                st.markdown(f"**{label}:**")
                                st.image(value, use_container_width=True)
                                st.caption(value)
                            else:
                                st.markdown(f"**{label}:** [{value}]({value})")
                        elif key in LINK_KEYS:
                            st.markdown(f"**{label}:** [{value}]({value})")
                        else:
                            st.markdown(f"**{label}:**")
                            st.code(value, language=None, wrap_lines=True)

                    # Footer: provider + tag chips + date + action buttons
                    footer_col1, footer_col2, footer_col3 = st.columns([6, 1, 1])
                    with footer_col1:
                        # Render provider
                        if entry["provider"]:
                            st.caption(f"🤖 {entry['provider']}")

                        # Render tags as inline chips using badge-style markdown
                        if entry["category"]:
                            tags = [t.strip() for t in entry["category"].split(",") if t.strip()]
                            chips = " ".join(f"`{tag}`" for tag in tags)
                            st.markdown(chips)

                        st.caption(f"🕐 {str(entry['created_at']).split('.')[0]}")
                    with footer_col2:
                        if st.button("✏️ Edit", key=f"edit_{entry['id']}", use_container_width=True):
                            st.session_state.editing_entry_id = entry["id"]
                            st.rerun()
                    with footer_col3:
                        if st.button("🗑️ Delete", key=f"delete_{entry['id']}", use_container_width=True):
                            delete_entry(entry["id"], user_id)
                            st.rerun()