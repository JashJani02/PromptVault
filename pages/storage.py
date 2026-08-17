import streamlit as st
from db import add_entry, get_entries, delete_entry, FIELDS, PROVIDERS


def render():
    st.title("🗂️ Storage")

    user_id = st.session_state.user_id

    # ---------- Add Entry ----------
    with st.expander("➕ Add Entry", expanded=True):
        st.caption("Fill in whichever fields apply. Leave the rest blank.")
        col1, col2 = st.columns(2)
        with col1:
            provider_choice = st.selectbox(
                "Provider (optional)", ["None"] + PROVIDERS, key="provider_choice"
            )
        with col2:
            custom_provider = ""
            if provider_choice in ("Other", "Local / Self-hosted"):
                custom_provider = st.text_input(
                    "Specify provider / harness",
                    placeholder="e.g. Llama 3 via Ollama, custom agent, etc.",
                    key="custom_provider",
                )

        with st.form("add_entry_form", clear_on_submit=True):
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

            category = st.text_input("Category (optional)", placeholder="e.g. Coding, Writing")

            submitted = st.form_submit_button("Save Entry", use_container_width=True)

            if submitted:
                has_content = any(v.strip() for v in values.values() if v)
                if has_content:
                    if provider_choice == "None":
                        provider = None
                    elif custom_provider.strip():
                        provider = custom_provider.strip()
                    else:
                        provider = provider_choice
                    add_entry(user_id, values, category or None, provider)
                    st.success("✅ Saved!")
                    st.rerun()
                else:
                    st.error("Fill in at least one field before saving.")

    st.divider()

    # ---------- View Entries ----------
    entries = get_entries(user_id)

    if not entries:
        st.info("No entries yet. Add one above!")
        return

    st.caption(f"{len(entries)} entries saved")

    for entry in entries:
        with st.container(border=True):
            for key, label in FIELDS:
                value = entry[key]
                if not value:
                    continue
                if key in ("image_url", "video_url", "chat_link", "artifact_link"):
                    st.markdown(f"**{label}:** [{value}]({value})")
                else:
                    st.markdown(f"**{label}:**")
                    st.write(value)

            footer_col1, footer_col2 = st.columns([7, 1])
            with footer_col1:
                tags = []
                if entry["provider"]:
                    tags.append(entry["provider"])
                if entry["category"]:
                    tags.append(entry["category"])
                caption = f"Saved: {entry['created_at']}"
                if tags:
                    caption += " · " + " · ".join(tags)
                st.caption(caption)
            with footer_col2:
                if st.button("🗑️ Delete", key=f"delete_{entry['id']}", use_container_width=True):
                    delete_entry(entry["id"], user_id)
                    st.rerun()