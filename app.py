import streamlit as st
import streamlit_authenticator as stauth
import json
import os
from datetime import datetime
from note_manager import NoteManager
from pdf_generator import PDFGenerator


# --- Authentication Setup ---
credentials = {
    "usernames": {
        "user1": {"name": "User One", "password": "password1"},
        "user2": {"name": "User Two", "password": "password2"},
    }
}
authenticator = stauth.Authenticate(
    credentials,
    "note_app_cookie", "abcdef", cookie_expiry_days=30
)
name, authentication_status, username = authenticator.login("Login", "sidebar")
if not authentication_status:
    st.stop()

# Initialize session state per user
user_notes_file = f"data/notes_{username}.json"
if 'note_manager' not in st.session_state or st.session_state.get('user_notes_file') != user_notes_file:
    st.session_state.note_manager = NoteManager(user_notes_file)
    st.session_state.user_notes_file = user_notes_file
if 'pdf_generator' not in st.session_state:
    st.session_state.pdf_generator = PDFGenerator()
if 'current_note_id' not in st.session_state:
    st.session_state.current_note_id = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

def main():
    st.set_page_config(
        page_title="Note Taking App",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("📝 Note Taking App")
    st.markdown("---")
    
    # Sidebar for navigation and note list
    with st.sidebar:
        st.header("📚 My Notes")
        
        # Create new note button
        if st.button("➕ New Note", use_container_width=True):
            st.session_state.current_note_id = None
            st.session_state.edit_mode = True
            st.rerun()
        
        st.markdown("---")
        
        # Search functionality
        search_query = st.text_input("🔍 Search notes", placeholder="Enter keywords...")
        
        # Load and display notes
        notes = st.session_state.note_manager.get_all_notes()
        
        # Filter notes based on search
        if search_query:
            filtered_notes = [
                note for note in notes 
                if search_query.lower() in note['title'].lower() or 
                   search_query.lower() in note['content'].lower()
            ]
        else:
            filtered_notes = notes
        
        if not filtered_notes:
            if search_query:
                st.info("No notes found matching your search.")
            else:
                st.info("No notes yet. Create your first note!")
        else:
            # Display notes list
            for note in filtered_notes:
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(
                        f"📄 {note['title'][:30]}{'...' if len(note['title']) > 30 else ''}",
                        key=f"note_{note['id']}",
                        use_container_width=True
                    ):
                        st.session_state.current_note_id = note['id']
                        st.session_state.edit_mode = False
                        st.rerun()
                
                with col2:
                    if st.button("🗑️", key=f"delete_{note['id']}", help="Delete note"):
                        if st.session_state.note_manager.delete_note(note['id']):
                            if st.session_state.current_note_id == note['id']:
                                st.session_state.current_note_id = None
                            st.success("Note deleted!")
                            st.rerun()
                
                # Show creation date
                created_date = datetime.fromisoformat(note['created_at']).strftime("%m/%d/%y %H:%M")
                st.caption(f"Created: {created_date}")
                st.markdown("---")
        
        # Export options
        if notes:
            st.header("📤 Export Options")
            
            # Export current note
            if st.session_state.current_note_id:
                if st.button("📄 Export Current Note to PDF", use_container_width=True):
                    current_note = st.session_state.note_manager.get_note(st.session_state.current_note_id)
                    if current_note:
                        pdf_bytes = st.session_state.pdf_generator.generate_single_note_pdf(current_note)
                        st.download_button(
                            label="💾 Download PDF",
                            data=pdf_bytes,
                            file_name=f"{current_note['title']}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
            
            # Export all notes
            if st.button("📚 Export All Notes to PDF", use_container_width=True):
                pdf_bytes = st.session_state.pdf_generator.generate_all_notes_pdf(notes)
                st.download_button(
                    label="💾 Download All Notes PDF",
                    data=pdf_bytes,
                    file_name=f"all_notes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    
    # Main content area
    if st.session_state.edit_mode or st.session_state.current_note_id is None:
        show_note_editor()
    else:
        show_note_viewer()

def show_note_editor():
    """Display the note editor interface"""
    st.header("✍️ Write Your Note")
    
    # Get current note if editing existing one
    current_note = None
    if st.session_state.current_note_id:
        current_note = st.session_state.note_manager.get_note(st.session_state.current_note_id)
    
    # Note title input
    title = st.text_input(
        "📝 Note Title",
        value=current_note['title'] if current_note else "",
        placeholder="Enter your note title..."
    )
    
    # Markdown formatting toolbar
    st.markdown("### ✍️ Note Content")
    
    # Enhanced formatting toolbar with better styling
    st.markdown("### ✨ Quick Formatting Tools")
    
    # Add custom CSS for better button styling
    st.markdown("""
    <style>
    div.stButton > button {
        height: 45px;
        font-weight: bold;
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        transition: all 0.3s;
    }
    div.stButton > button:hover {
        border-color: #1976d2;
        background-color: #f5f5f5;
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Row 1: Basic formatting with better visual labels
    row1_col1, row1_col2, row1_col3, row1_col4, row1_col5, row1_col6, row1_col7, row1_col8 = st.columns(8)
    with row1_col1:
        if st.button("**B**", help="Bold Text", key="bold_btn", use_container_width=True):
            st.session_state.format_hint = "**bold text**"
            st.session_state.hint_explanation = "Use **text** to make text bold"
    with row1_col2:
        if st.button("*I*", help="Italic Text", key="italic_btn", use_container_width=True):
            st.session_state.format_hint = "*italic text*"
            st.session_state.hint_explanation = "Use *text* to make text italic"
    with row1_col3:
        if st.button("~~S~~", help="Strikethrough", key="strike_btn", use_container_width=True):
            st.session_state.format_hint = "~~strikethrough~~"
            st.session_state.hint_explanation = "Use ~~text~~ to cross out text"
    with row1_col4:
        if st.button("`Code`", help="Inline Code", key="code_btn", use_container_width=True):
            st.session_state.format_hint = "`inline code`"
            st.session_state.hint_explanation = "Use `code` for inline code formatting"
    with row1_col5:
        if st.button("# H1", help="Large Heading", key="h1_btn", use_container_width=True):
            st.session_state.format_hint = "# Large Heading"
            st.session_state.hint_explanation = "Use # for the largest heading"
    with row1_col6:
        if st.button("## H2", help="Medium Heading", key="h2_btn", use_container_width=True):
            st.session_state.format_hint = "## Medium Heading"
            st.session_state.hint_explanation = "Use ## for medium-sized headings"
    with row1_col7:
        if st.button("### H3", help="Small Heading", key="h3_btn", use_container_width=True):
            st.session_state.format_hint = "### Small Heading"
            st.session_state.hint_explanation = "Use ### for smaller headings"
    with row1_col8:
        if st.button("🔗 Link", help="Web Link", key="link_btn", use_container_width=True):
            st.session_state.format_hint = "[link text](https://example.com)"
            st.session_state.hint_explanation = "Use [text](url) to create clickable links"
    
    # Row 2: Lists and advanced formatting with better visual labels
    row2_col1, row2_col2, row2_col3, row2_col4, row2_col5, row2_col6, row2_col7, row2_col8 = st.columns(8)
    with row2_col1:
        if st.button("• List", help="Bullet List", key="bullet_btn", use_container_width=True):
            st.session_state.format_hint = "• First item\n• Second item\n• Third item"
            st.session_state.hint_explanation = "Use • or - for bullet points"
    with row2_col2:
        if st.button("1. List", help="Numbered List", key="num_btn", use_container_width=True):
            st.session_state.format_hint = "1. First item\n2. Second item\n3. Third item"
            st.session_state.hint_explanation = "Use 1. 2. 3. for numbered lists"
    with row2_col3:
        if st.button("💬 Quote", help="Quote Block", key="quote_btn", use_container_width=True):
            st.session_state.format_hint = "> This is a quote\n> Multi-line quote"
            st.session_state.hint_explanation = "Use > at start of line for quotes"
    with row2_col4:
        if st.button("</> Code", help="Code Block", key="codeblock_btn", use_container_width=True):
            st.session_state.format_hint = "```\ncode block\nmore code\n```"
            st.session_state.hint_explanation = "Use ``` to wrap code blocks"
    with row2_col5:
        if st.button("━━━", help="Horizontal Line", key="hr_btn", use_container_width=True):
            st.session_state.format_hint = "---"
            st.session_state.hint_explanation = "Use --- for horizontal divider lines"
    with row2_col6:
        if st.button("📊 Table", help="Table", key="table_btn", use_container_width=True):
            st.session_state.format_hint = "| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |"
            st.session_state.hint_explanation = "Use | to create table columns"
    with row2_col7:
        if st.button("☑️ Check", help="Checklist", key="check_btn", use_container_width=True):
            st.session_state.format_hint = "- [ ] Unchecked item\n- [x] Checked item"
            st.session_state.hint_explanation = "Use - [ ] for checkboxes"
    with row2_col8:
        if st.button("⚡ Auto", help="Smart Templates", key="auto_btn", use_container_width=True):
            # Auto-suggest helpful templates
            st.session_state.format_hint = "# Title\n\n**Summary:** Brief overview\n\n## Main Points\n• Point 1\n• Point 2\n\n**Conclusion:** Final thoughts"
            st.session_state.hint_explanation = "Smart template: Complete note structure with headings, bold text, and bullet points"
    
    # Enhanced hint system with explanation and examples
    if hasattr(st.session_state, 'format_hint'):
        hint_col1, hint_col2 = st.columns([2, 1])
        
        with hint_col1:
            st.success(f"✨ **Copy this format:**")
            st.code(st.session_state.format_hint, language="markdown")
            
        with hint_col2:
            if hasattr(st.session_state, 'hint_explanation'):
                st.info(f"💡 {st.session_state.hint_explanation}")
        
        # Auto-clear hint after a few seconds (simulate by user interaction)
        if st.button("✅ Got it!", key="clear_hint"):
            if hasattr(st.session_state, 'format_hint'):
                delattr(st.session_state, 'format_hint')
            if hasattr(st.session_state, 'hint_explanation'):
                delattr(st.session_state, 'hint_explanation')
            st.rerun()
    
    # Markdown editor with enhanced placeholder and keyboard shortcuts
    content = st.text_area(
        "Write your note with markdown formatting:",
        value=current_note['content'] if current_note else "",
        height=350,
        placeholder="""💡 Start writing your note here...

⚡ Quick Tips:
• Use the buttons above for instant formatting
• Press Tab to indent lists
• **Bold**, *italic*, ~~strikethrough~~
• Create tables with | pipes |
• Use --- for horizontal lines
• Add [ ] for checkboxes

🎯 Try clicking the ⚡Auto button for smart templates!
🔍 Live preview shows below as you type!""",
        help="💫 Pro tip: Click any formatting button above for instant examples and copy-paste templates!"
    )
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 Save Note", type="primary", use_container_width=True):
            if title.strip() and content.strip():
                if st.session_state.current_note_id:
                    # Update existing note
                    success = st.session_state.note_manager.update_note(
                        st.session_state.current_note_id,
                        title.strip(),
                        content.strip()
                    )
                    if success:
                        st.success("Note updated successfully!")
                        st.session_state.edit_mode = False
                        st.rerun()
                    else:
                        st.error("Failed to update note.")
                else:
                    # Create new note
                    note_id = st.session_state.note_manager.create_note(title.strip(), content.strip())
                    if note_id:
                        st.success("Note saved successfully!")
                        st.session_state.current_note_id = note_id
                        st.session_state.edit_mode = False
                        st.rerun()
                    else:
                        st.error("Failed to save note.")
            else:
                st.warning("Please enter both title and content.")
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.edit_mode = False
            st.rerun()
    
    # Enhanced Real-time Preview section
    if title.strip() or content.strip():
        st.markdown("---")
        preview_header_col1, preview_header_col2 = st.columns([3, 1])
        
        with preview_header_col1:
            st.header("👀 Live Preview")
        
        with preview_header_col2:
            # Toggle preview mode
            preview_mode = st.selectbox("🔍 View", ["Side by Side", "Preview Only", "Raw Only"], key="preview_mode")
        
        if content.strip():
            if preview_mode == "Side by Side":
                preview_col1, preview_col2 = st.columns([1, 1])
                
                with preview_col1:
                    st.subheader("📝 Raw Markdown")
                    display_content = content[:1000] + "..." if len(content) > 1000 else content
                    st.code(display_content, language="markdown")
                
                with preview_col2:
                    st.subheader("🎨 Rendered Preview")
                    if title.strip():
                        st.markdown(f"# {title}")
                    # Preserve line breaks exactly as typed
                    content_with_breaks = content.replace('\n', '<br>')
                    st.markdown(content_with_breaks, unsafe_allow_html=True)
            
            elif preview_mode == "Preview Only":
                if title.strip():
                    st.markdown(f"# {title}")
                # Preserve line breaks exactly as typed
                content_with_breaks = content.replace('\n', '<br>')
                st.markdown(content_with_breaks, unsafe_allow_html=True)
            
            else:  # Raw Only
                st.code(content, language="markdown")
            
        else:
            if title.strip():
                st.markdown(f"# {title}")
                st.info("✨ Start typing content to see the live preview...")

def show_note_viewer():
    """Display the note viewer interface"""
    if st.session_state.current_note_id:
        note = st.session_state.note_manager.get_note(st.session_state.current_note_id)
        if note:
            # Note header with actions
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.header(note['title'])
            
            with col2:
                if st.button("✏️ Edit", use_container_width=True):
                    st.session_state.edit_mode = True
                    st.rerun()
            
            with col3:
                if st.button("📄 Export PDF", use_container_width=True):
                    pdf_bytes = st.session_state.pdf_generator.generate_single_note_pdf(note)
                    st.download_button(
                        label="💾 Download",
                        data=pdf_bytes,
                        file_name=f"{note['title']}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            
            # Note metadata
            created_date = datetime.fromisoformat(note['created_at']).strftime("%B %d, %Y at %I:%M %p")
            updated_date = datetime.fromisoformat(note['updated_at']).strftime("%B %d, %Y at %I:%M %p")
            
            st.caption(f"📅 Created: {created_date}")
            if note['created_at'] != note['updated_at']:
                st.caption(f"🔄 Last updated: {updated_date}")
            
            st.markdown("---")
            
            # Note content with enhanced markdown rendering (preserving line breaks)
            content_with_breaks = note['content'].replace('\n', '<br>')
            st.markdown(content_with_breaks, unsafe_allow_html=True)
            
            
        else:
            st.error("Note not found.")
            st.session_state.current_note_id = None
    else:
        # Welcome screen
        st.header("🌟 Welcome to Your Markdown Note Taking App")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("""
            ### ✨ Powerful Features
            
            - 📝 **Rich Markdown Support** - Format text beautifully
            - 🔍 **Instant Search** - Find notes quickly
            - 📄 **PDF Export** - Professional document output
            - 📱 **Cross-Platform** - Works on all devices
            - 💾 **Auto-Save** - Never lose your work
            - 👀 **Live Preview** - See formatting in real-time
            """)
        
        with col2:
            st.markdown("""
            ### 🚀 Quick Start Guide
            
            1. **Create** - Click "➕ New Note" in sidebar
            2. **Write** - Use markdown formatting tools
            3. **Preview** - See your formatted text live
            4. **Save** - Your notes are stored automatically
            5. **Export** - Download as PDF anytime
            """)
        
        st.markdown("---")
        
        # Enhanced markdown cheat sheet with more examples
        st.header("📚 Markdown Quick Reference")
        
        ref_tab1, ref_tab2, ref_tab3 = st.tabs(["📝 Basic", "📈 Advanced", "⚡ Pro Tips"])
        
        with ref_tab1:
            ref_col1, ref_col2 = st.columns([1, 1])
            with ref_col1:
                st.markdown("""
                **Text Formatting:**
                ```markdown
                # Heading 1
                ## Heading 2
                ### Heading 3
                **Bold text**
                *Italic text*
                ~~Strikethrough~~
                `Inline code`
                ```
                """)
            with ref_col2:
                st.markdown("""
                **Lists & Links:**
                ```markdown
                • Bullet point
                - Another bullet
                1. Numbered list
                2. Second item
                
                [Link](https://example.com)
                > Quote text
                ```
                """)
        
        with ref_tab2:
            adv_col1, adv_col2 = st.columns([1, 1])
            with adv_col1:
                st.markdown("""
                **Tables:**
                ```markdown
                | Header 1 | Header 2 |
                |----------|----------|
                | Cell 1   | Cell 2   |
                | Cell 3   | Cell 4   |
                ```
                """)
            with adv_col2:
                st.markdown("""
                **Code & Checklists:**
                ```markdown
                ```python
                def hello():
                    print("Hello!")
                ```
                
                - [ ] Todo item
                - [x] Completed
                ---
                ```
                """)
        
        with ref_tab3:
            st.markdown("""
            **🚀 Pro Tips for Faster Writing:**
            
            1. **Use the toolbar buttons** - Click any button to get instant examples
            2. **Try the ⚡Auto button** - Get smart templates based on your content
            3. **Combine formatting** - Use **bold** inside *italic* or in `code`
            4. **Tables made easy** - Start with | Header | and add rows below
            5. **Quick checklists** - Use - [ ] for todos, - [x] for completed
            6. **Horizontal dividers** - Use --- to separate sections
            
            **Keyboard Tips:**
            - Use Tab to indent list items
            - Double-space at end of line for line break
            - Start lines with > for quotes
            """)
        
        # Quick action panel for common patterns
        st.markdown("### ⚡ Quick Actions")
        quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)
        
        with quick_col1:
            if st.button("📝 Meeting Notes", use_container_width=True):
                st.session_state.quick_template = "meeting"
        with quick_col2:
            if st.button("✅ Todo List", use_container_width=True):
                st.session_state.quick_template = "todo"
        with quick_col3:
            if st.button("📊 Report", use_container_width=True):
                st.session_state.quick_template = "report"
        with quick_col4:
            if st.button("📚 Study Notes", use_container_width=True):
                st.session_state.quick_template = "study"
        
        # Show template if selected
        if hasattr(st.session_state, 'quick_template'):
            if st.session_state.quick_template == "meeting":
                template = "## Meeting Notes\n**Date:** $(date)\n**Attendees:** \n- Person 1\n- Person 2\n\n### Agenda\n1. Topic 1\n2. Topic 2\n\n### Key Points\n• Important discussion\n• Decision made\n\n### Action Items\n- [ ] Task for person 1\n- [ ] Follow up on topic 2"
            elif st.session_state.quick_template == "todo":
                template = "# Todo List\n\n## 🚀 High Priority\n- [ ] Important task 1\n- [ ] Important task 2\n\n## 📅 Today\n- [ ] Task to complete today\n- [x] Already completed\n\n## 🕰️ Later\n- [ ] Future task\n- [ ] Nice to have"
            elif st.session_state.quick_template == "report":
                template = "# Project Report\n\n## Executive Summary\n**Brief overview of the project status and key findings.**\n\n## Key Metrics\n| Metric | Value | Status |\n|--------|-------|--------|\n| Progress | 75% | ✅ On track |\n| Budget | $50K | ⚠️ Review |\n\n## Recommendations\n1. **Continue** current approach\n2. **Review** budget allocation\n3. **Implement** new strategies"
            else:  # study
                template = "# Study Notes\n\n## 🎯 Learning Objectives\n- Understand key concepts\n- Apply knowledge practically\n\n## 📝 Key Concepts\n\n### Concept 1\n**Definition:** Brief explanation\n\n**Examples:**\n• Example 1\n• Example 2\n\n### Concept 2\n> Important quote or principle\n\n## 🧠 Memory Aids\n- **Acronym:** ABC = Always Be Coding\n- **Visual:** Imagine a flowchart\n\n## ❓ Questions for Review\n- [ ] What is the main idea?\n- [ ] How does this apply?"
            
            st.success("✨ **Template Ready!** Copy this to get started:")
            st.code(template, language="markdown")
            
            if st.button("✅ Got the template!"):
                delattr(st.session_state, 'quick_template')
                st.rerun()
        
        st.info("💡 **Tip:** Use the formatting toolbar in the editor for instant markdown examples!")
        st.success("🎯 **Ready to start?** Click '➕ New Note' in the sidebar to create your first note!")

if __name__ == "__main__":
    main()
