import io
from datetime import datetime
from typing import List, Dict
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfgen import canvas
import re

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom styles for PDF generation"""
        # Custom title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=12,
            textColor='#2C3E50'
        ))
        
        # Custom heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=8,
            textColor='#34495E'
        ))
        
        # Custom body style with better spacing
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            spaceBefore=2,
            leftIndent=0,
            rightIndent=0
        ))
        
        # Style for metadata
        self.styles.add(ParagraphStyle(
            name='MetaData',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor='#7F8C8D',
            spaceAfter=12
        ))
        
        # Style for note separator
        self.styles.add(ParagraphStyle(
            name='Separator',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor='#BDC3C7',
            alignment=TA_CENTER,
            spaceAfter=12,
            spaceBefore=12
        ))
    
    def clean_content(self, content: str) -> str:
        """Clean and prepare content for PDF with enhanced markdown support"""
        # Handle headings first
        content = re.sub(r'^### (.*?)$', r'<b><font size="12">\1</font></b>', content, flags=re.MULTILINE)  # H3
        content = re.sub(r'^## (.*?)$', r'<b><font size="14">\1</font></b>', content, flags=re.MULTILINE)   # H2
        content = re.sub(r'^# (.*?)$', r'<b><font size="16">\1</font></b>', content, flags=re.MULTILINE)    # H1
        
        # Handle text formatting
        content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)    # Bold
        content = re.sub(r'\*(.*?)\*', r'<i>\1</i>', content)        # Italic
        content = re.sub(r'~~(.*?)~~', r'<strike>\1</strike>', content)  # Strikethrough
        content = re.sub(r'`([^`]+)`', r'<font face="Courier">\1</font>', content)  # Inline code
        
        # Handle lists
        content = re.sub(r'^\• ', r'• ', content, flags=re.MULTILINE)        # Bullet points (•)
        content = re.sub(r'^- ', r'• ', content, flags=re.MULTILINE)         # Bullet points (-)
        content = re.sub(r'^\d+\. ', r'• ', content, flags=re.MULTILINE)     # Convert numbered lists to bullets for simplicity
        
        # Handle quotes
        content = re.sub(r'^> (.*?)$', r'<i>"  \1  "</i>', content, flags=re.MULTILINE)
        
        # Handle code blocks (better approach with content preservation)
        def replace_code_block(match):
            code_content = match.group(0).replace('```', '').strip()
            # Take first 100 chars of code for readability
            if len(code_content) > 100:
                code_content = code_content[:100] + "..."
            return f'<font face="Courier" size="9">{code_content}</font>'
        content = re.sub(r'```[\s\S]*?```', replace_code_block, content)
        
        # Handle tables (convert to simple format)
        def replace_table(match):
            table_text = match.group(0)
            lines = table_text.split('\n')
            result = []
            for line in lines:
                if '|' in line and not line.strip().startswith('|--'):
                    cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                    if cells:
                        result.append(' • '.join(cells))
            return '<br/>'.join(result)
        
        content = re.sub(r'\|.*?\|[\s\S]*?(?=\n\n|\n[^|]|\Z)', replace_table, content, flags=re.MULTILINE)
        
        # Handle checklists
        content = re.sub(r'^- \[x\] (.*?)$', r'✓ \1', content, flags=re.MULTILINE)  # Checked
        content = re.sub(r'^- \[ \] (.*?)$', r'☐ \1', content, flags=re.MULTILINE)  # Unchecked
        
        # Handle horizontal rules
        content = re.sub(r'^---+$', r'_' * 50, content, flags=re.MULTILINE)
        
        # Handle links (extract just the text for PDF)
        content = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', content)
        
        # Handle line breaks
        content = content.replace('\n\n', '<br/><br/>')
        content = content.replace('\n', '<br/>')
        
        return content
    
    def generate_single_note_pdf(self, note: Dict) -> bytes:
        """Generate PDF for a single note"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=1*inch,
            bottomMargin=1*inch,
            leftMargin=1*inch,
            rightMargin=1*inch
        )
        
        story = []
        
        # Add title
        title = Paragraph(note['title'], self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Add metadata
        created_date = datetime.fromisoformat(note['created_at']).strftime("%B %d, %Y at %I:%M %p")
        updated_date = datetime.fromisoformat(note['updated_at']).strftime("%B %d, %Y at %I:%M %p")
        
        meta_text = f"Created: {created_date}"
        if note['created_at'] != note['updated_at']:
            meta_text += f" | Last Updated: {updated_date}"
        
        metadata = Paragraph(meta_text, self.styles['MetaData'])
        story.append(metadata)
        story.append(Spacer(1, 12))
        
        # Add horizontal line
        separator = Paragraph("─" * 50, self.styles['Separator'])
        story.append(separator)
        
        # Add content
        clean_content = self.clean_content(note['content'])
        
        # Split content into paragraphs
        paragraphs = clean_content.split('<br/><br/>')
        
        for paragraph_text in paragraphs:
            if paragraph_text.strip():
                paragraph = Paragraph(paragraph_text.strip(), self.styles['CustomBody'])
                story.append(paragraph)
                story.append(Spacer(1, 6))
        
        # Build PDF
        try:
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
        except Exception as e:
            print(f"Error generating PDF: {e}")
            # Return a simple error PDF
            return self.generate_error_pdf("Error generating PDF")
    
    def generate_all_notes_pdf(self, notes: List[Dict]) -> bytes:
        """Generate PDF for all notes"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=1*inch,
            bottomMargin=1*inch,
            leftMargin=1*inch,
            rightMargin=1*inch
        )
        
        story = []
        
        # Add cover page
        cover_title = Paragraph("My Notes Collection", self.styles['CustomTitle'])
        story.append(cover_title)
        story.append(Spacer(1, 12))
        
        # Add generation date
        generation_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        date_text = f"Generated on: {generation_date}"
        date_para = Paragraph(date_text, self.styles['MetaData'])
        story.append(date_para)
        story.append(Spacer(1, 12))
        
        # Add summary
        summary_text = f"Total Notes: {len(notes)}"
        summary_para = Paragraph(summary_text, self.styles['CustomBody'])
        story.append(summary_para)
        story.append(Spacer(1, 24))
        
        # Add table of contents
        toc_title = Paragraph("Table of Contents", self.styles['CustomHeading'])
        story.append(toc_title)
        story.append(Spacer(1, 12))
        
        for i, note in enumerate(notes, 1):
            created_date = datetime.fromisoformat(note['created_at']).strftime("%m/%d/%Y")
            toc_entry = f"{i}. {note['title']} ({created_date})"
            toc_para = Paragraph(toc_entry, self.styles['CustomBody'])
            story.append(toc_para)
        
        story.append(PageBreak())
        
        # Add each note
        for i, note in enumerate(notes, 1):
            # Note number and title
            note_title = f"{i}. {note['title']}"
            title_para = Paragraph(note_title, self.styles['CustomTitle'])
            story.append(title_para)
            story.append(Spacer(1, 12))
            
            # Add metadata
            created_date = datetime.fromisoformat(note['created_at']).strftime("%B %d, %Y at %I:%M %p")
            updated_date = datetime.fromisoformat(note['updated_at']).strftime("%B %d, %Y at %I:%M %p")
            
            meta_text = f"Created: {created_date}"
            if note['created_at'] != note['updated_at']:
                meta_text += f" | Last Updated: {updated_date}"
            
            metadata = Paragraph(meta_text, self.styles['MetaData'])
            story.append(metadata)
            story.append(Spacer(1, 8))
            
            # Add content
            clean_content = self.clean_content(note['content'])
            
            # Split content into paragraphs
            paragraphs = clean_content.split('<br/><br/>')
            
            for paragraph_text in paragraphs:
                if paragraph_text.strip():
                    paragraph = Paragraph(paragraph_text.strip(), self.styles['CustomBody'])
                    story.append(paragraph)
                    story.append(Spacer(1, 6))
            
            # Add separator between notes (except for the last one)
            if i < len(notes):
                story.append(Spacer(1, 24))
                separator = Paragraph("─" * 80, self.styles['Separator'])
                story.append(separator)
                story.append(Spacer(1, 24))
        
        # Build PDF
        try:
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
        except Exception as e:
            print(f"Error generating all notes PDF: {e}")
            # Return a simple error PDF
            return self.generate_error_pdf("Error generating notes collection PDF")
    
    def generate_error_pdf(self, error_message: str) -> bytes:
        """Generate a simple error PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        story = []
        error_title = Paragraph("PDF Generation Error", self.styles['CustomTitle'])
        story.append(error_title)
        story.append(Spacer(1, 12))
        
        error_para = Paragraph(error_message, self.styles['CustomBody'])
        story.append(error_para)
        
        try:
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
        except:
            # If even error PDF fails, return empty bytes
            return b''
