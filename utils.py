from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import random
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

def generate_quote_card(text, author, book_title, theme="dark"):
    # Configuration
    width = 1080
    height = 1080
    padding = 100
    
    # Colors
    if theme == "dark":
        bg_color = (30, 30, 30)
        text_color = (255, 255, 255)
        accent_color = (100, 200, 200) # Teal-ish
    elif theme == "light":
        bg_color = (240, 240, 240)
        text_color = (30, 30, 30)
        accent_color = (0, 120, 120)
    elif theme == "sepia":
        bg_color = (244, 228, 188)
        text_color = (60, 40, 20)
        accent_color = (100, 50, 0)
    else:
        # Random gradient-ish solid color
        bg_color = (random.randint(50, 100), random.randint(50, 100), random.randint(100, 150))
        text_color = (255, 255, 255)
        accent_color = (200, 200, 200)

    # Create Image
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Load Fonts (Try to find a nice system font, fallback to default)
    try:
        # Windows paths
        font_path = "C:\\Windows\\Fonts\\arial.ttf"
        if not os.path.exists(font_path):
            font_path = "arial.ttf" # Linux/Mac fallback attempt
            
        font_text = ImageFont.truetype(font_path, 60)
        font_author = ImageFont.truetype(font_path, 40)
        font_book = ImageFont.truetype(font_path, 30)
    except:
        font_text = ImageFont.load_default()
        font_author = ImageFont.load_default()
        font_book = ImageFont.load_default()

    # Wrap Text
    # Estimate chars per line (rough approx)
    chars_per_line = 30 
    lines = textwrap.wrap(text, width=chars_per_line)
    
    # Calculate Text Height
    # ascent, descent = font_text.getmetrics()
    # line_height = ascent + descent + 20
    line_height = 80 # Fixed for simplicity with arial 60
    total_text_height = len(lines) * line_height
    
    # Draw Text Centered
    current_y = (height - total_text_height) / 2 - 50
    
    # Draw Quote Icon
    # draw.text((padding, current_y - 100), '"', font=ImageFont.truetype(font_path, 150), fill=accent_color)

    for line in lines:
        # Get text width using getbbox (left, top, right, bottom)
        bbox = draw.textbbox((0, 0), line, font=font_text)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) / 2
        draw.text((x, current_y), line, font=font_text, fill=text_color)
        current_y += line_height

    # Draw Author & Book
    current_y += 50
    author_text = f"- {author}"
    bbox = draw.textbbox((0, 0), author_text, font=font_author)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) / 2
    draw.text((x, current_y), author_text, font=font_author, fill=accent_color)
    
    current_y += 60
    book_text = book_title
    bbox = draw.textbbox((0, 0), book_text, font=font_book)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) / 2
    draw.text((x, current_y), book_text, font=font_book, fill=text_color)

    # Save
    output_dir = "quote_cards"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = f"quote_{random.randint(1000,9999)}.png"
    filepath = os.path.join(output_dir, filename)
    img.save(filepath)
    
    return filepath

def generate_book_report_pdf(book_data, quotes, vocab, notes, output_path):
    """
    Generates a PDF report for a book.
    book_data: tuple/list from database
    quotes: list of quote tuples
    vocab: list of vocab tuples
    notes: string
    """
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # Register a font that supports Turkish characters if possible
    # Fallback to Helvetica which has basic support, or try to load Arial
    try:
        pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
        font_name = 'Arial'
    except:
        font_name = 'Helvetica'

    # Header
    c.setFillColor(colors.teal)
    c.rect(0, height - 100, width, 100, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont(font_name, 24)
    c.drawString(30, height - 60, "Kitap Karnesi")
    
    # Book Info
    c.setFillColor(colors.black)
    c.setFont(font_name, 18)
    title = book_data[1]
    c.drawString(30, height - 140, title)
    
    c.setFont(font_name, 14)
    c.setFillColor(colors.grey)
    author = book_data[2]
    c.drawString(30, height - 165, f"Yazar: {author}")
    
    # Rating
    rating = book_data[7] if book_data[7] else 0
    c.setFillColor(colors.orange)
    c.drawString(width - 150, height - 140, f"Puan: {rating}/5")
    
    y = height - 200
    
    # Summary
    summary = book_data[9]
    if summary:
        c.setFillColor(colors.teal)
        c.setFont(font_name, 14)
        c.drawString(30, y, "Özet")
        c.line(30, y-5, 100, y-5)
        y -= 25
        
        c.setFillColor(colors.black)
        c.setFont(font_name, 10)
        lines = textwrap.wrap(summary, width=90)
        for line in lines:
            c.drawString(30, y, line)
            y -= 15
        y -= 20

    # Notes
    if notes:
        if y < 100: c.showPage(); y = height - 50
        c.setFillColor(colors.teal)
        c.setFont(font_name, 14)
        c.drawString(30, y, "Kişisel Notlar")
        c.line(30, y-5, 150, y-5)
        y -= 25
        
        c.setFillColor(colors.black)
        c.setFont(font_name, 10)
        lines = textwrap.wrap(notes, width=90)
        for line in lines:
            c.drawString(30, y, line)
            y -= 15
        y -= 20

    # Quotes
    if quotes:
        if y < 100: c.showPage(); y = height - 50
        c.setFillColor(colors.teal)
        c.setFont(font_name, 14)
        c.drawString(30, y, "Alıntılar")
        c.line(30, y-5, 100, y-5)
        y -= 25
        
        c.setFillColor(colors.black)
        c.setFont(font_name, 10)
        for q in quotes:
            text = f'"{q[2]}"'
            page = f"(sf. {q[3]})" if q[3] else ""
            
            lines = textwrap.wrap(text, width=80)
            for line in lines:
                if y < 50: c.showPage(); y = height - 50
                c.drawString(40, y, line)
                y -= 15
            
            c.setFillColor(colors.grey)
            c.drawString(width - 100, y+15, page)
            c.setFillColor(colors.black)
            y -= 10
        y -= 20

    # Vocabulary
    if vocab:
        if y < 100: c.showPage(); y = height - 50
        c.setFillColor(colors.teal)
        c.setFont(font_name, 14)
        c.drawString(30, y, "Kelime Hazinesi")
        c.line(30, y-5, 150, y-5)
        y -= 25
        
        for v in vocab:
            if y < 50: c.showPage(); y = height - 50
            # Word
            c.setFillColor(colors.black)
            c.setFont(font_name, 11)
            c.drawString(40, y, v[3])
            
            # Definition
            c.setFont(font_name, 10)
            c.drawString(150, y, f": {v[4]}")
            y -= 15
            
            # Sentence
            if v[5]:
                c.setFillColor(colors.grey)
                c.setFont(font_name, 9)
                c.drawString(150, y, f"Örnek: {v[5]}")
                y -= 15
            y -= 5

    c.save()
    return output_path
