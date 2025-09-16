#!/usr/bin/env python3
"""
Extractor y limpiador de contenido WordPress para Julia Confecciones
Extrae productos, páginas y contenido útil del export XML
"""

import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime
import html

class WordPressExtractor:
    def __init__(self, xml_file):
        self.xml_file = xml_file
        self.tree = ET.parse(xml_file)
        self.root = self.tree.getroot()
        
    def clean_html(self, html_content):
        """Limpiar HTML y extraer texto plano"""
        if not html_content:
            return ""
        # Remover tags HTML pero mantener texto
        clean_text = re.sub(r'<[^>]+>', '', html_content)
        # Decodificar entidades HTML
        clean_text = html.unescape(clean_text)
        # Limpiar espacios múltiples
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return clean_text
    
    def extract_products(self):
        """Extraer productos con información limpia"""
        products = []
        
        for item in self.root.findall('.//item'):
            post_type = item.find('wp:post_type', {'wp': 'http://wordpress.org/export/1.2/'})
            
            if post_type is not None and post_type.text == 'product':
                product = {
                    'title': '',
                    'description': '',
                    'short_description': '',
                    'price': 0,
                    'sku': '',
                    'categories': [],
                    'images': [],
                    'attributes': {},
                    'stock_status': 'instock',
                    'content_raw': ''
                }
                
                # Título
                title_elem = item.find('title')
                if title_elem is not None:
                    product['title'] = title_elem.text or ''
                
                # Contenido y descripción corta
                content_elem = item.find('content:encoded', {'content': 'http://purl.org/rss/1.0/modules/content/'})
                excerpt_elem = item.find('excerpt:encoded', {'excerpt': 'http://wordpress.org/export/1.2/excerpt/'})
                
                if content_elem is not None:
                    product['content_raw'] = content_elem.text or ''
                    product['description'] = self.clean_html(content_elem.text)
                
                if excerpt_elem is not None:
                    product['short_description'] = self.clean_html(excerpt_elem.text)
                
                # Extraer metadatos de WooCommerce
                for postmeta in item.findall('wp:postmeta', {'wp': 'http://wordpress.org/export/1.2/'}):
                    meta_key = postmeta.find('wp:meta_key')
                    meta_value = postmeta.find('wp:meta_value')
                    
                    if meta_key is not None and meta_value is not None:
                        key = meta_key.text
                        value = meta_value.text
                        
                        if key == '_price':
                            try:
                                product['price'] = float(value) if value else 0
                            except:
                                product['price'] = 0
                        elif key == '_sku':
                            product['sku'] = value or ''
                        elif key == '_stock_status':
                            product['stock_status'] = value or 'instock'
                        elif key == '_thumbnail_id':
                            # Guardar ID de imagen para después
                            product['thumbnail_id'] = value
                
                # Extraer imágenes del contenido
                if product['content_raw']:
                    img_urls = re.findall(r'src="([^"]+\.(?:jpg|jpeg|png|gif))"', product['content_raw'])
                    product['images'] = list(set(img_urls))  # Remover duplicados
                
                # Extraer categorías
                for category in item.findall('category'):
                    domain = category.get('domain')
                    if domain == 'product_cat':
                        cat_name = category.text
                        if cat_name:
                            product['categories'].append(cat_name)
                
                # Limpiar título para variantes
                title_lower = product['title'].lower()
                if 'talla' in title_lower:
                    # Es una variante, extraer info
                    talla_match = re.search(r'talla\s+(\d+|[a-zA-Z]+)', title_lower)
                    if talla_match:
                        product['attributes']['talla'] = talla_match.group(1)
                
                products.append(product)
        
        return products
    
    def extract_pages(self):
        """Extraer páginas institucionales"""
        pages = []
        
        for item in self.root.findall('.//item'):
            post_type = item.find('wp:post_type', {'wp': 'http://wordpress.org/export/1.2/'})
            
            if post_type is not None and post_type.text == 'page':
                page = {
                    'title': '',
                    'content': '',
                    'content_raw': '',
                    'slug': '',
                    'template': '',
                    'images': []
                }
                
                # Título
                title_elem = item.find('title')
                if title_elem is not None:
                    page['title'] = title_elem.text or ''
                
                # Contenido
                content_elem = item.find('content:encoded', {'content': 'http://purl.org/rss/1.0/modules/content/'})
                if content_elem is not None:
                    page['content_raw'] = content_elem.text or ''
                    page['content'] = self.clean_html(content_elem.text)
                
                # Slug
                for postmeta in item.findall('wp:postmeta', {'wp': 'http://wordpress.org/export/1.2/'}):
                    meta_key = postmeta.find('wp:meta_key')
                    meta_value = postmeta.find('wp:meta_value')
                    
                    if meta_key is not None and meta_value is not None:
                        if meta_key.text == '_wp_page_template':
                            page['template'] = meta_value.text or ''
                        elif meta_key.text == '_wp_page_slug':
                            page['slug'] = meta_value.text or ''
                
                # Extraer imágenes
                if page['content_raw']:
                    img_urls = re.findall(r'src="([^"]+\.(?:jpg|jpeg|png|gif))"', page['content_raw'])
                    page['images'] = list(set(img_urls))
                
                # Filtrar páginas útiles (ignorar elementos de diseño)
                ignore_pages = [
                    'botones vacios', 'titles / dividers', 'grid style 2', 
                    'testimonials', 'buttons', 'about', 'map', 'simple slider',
                    'shop - category slider', 'shop - header', 'blog header'
                ]
                
                if page['title'].lower() not in [p.lower() for p in ignore_pages]:
                    pages.append(page)
        
        return pages
    
    def extract_posts(self):
        """Extraer posts de blog"""
        posts = []
        
        for item in self.root.findall('.//item'):
            post_type = item.find('wp:post_type', {'wp': 'http://wordpress.org/export/1.2/'})
            
            if post_type is not None and post_type.text == 'post':
                post = {
                    'title': '',
                    'content': '',
                    'excerpt': '',
                    'date': '',
                    'categories': [],
                    'images': []
                }
                
                # Título
                title_elem = item.find('title')
                if title_elem is not None:
                    post['title'] = title_elem.text or ''
                
                # Contenido
                content_elem = item.find('content:encoded', {'content': 'http://purl.org/rss/1.0/modules/content/'})
                excerpt_elem = item.find('excerpt:encoded', {'excerpt': 'http://wordpress.org/export/1.2/excerpt/'})
                
                if content_elem is not None:
                    content = content_elem.text or ''
                    post['content'] = self.clean_html(content)
                    # Extraer imágenes
                    img_urls = re.findall(r'src="([^"]+\.(?:jpg|jpeg|png|gif))"', content)
                    post['images'] = list(set(img_urls))
                
                if excerpt_elem is not None:
                    post['excerpt'] = self.clean_html(excerpt_elem.text)
                
                # Fecha
                date_elem = item.find('wp:post_date', {'wp': 'http://wordpress.org/export/1.2/'})
                if date_elem is not None:
                    post['date'] = date_elem.text or ''
                
                # Categorías
                for category in item.findall('category'):
                    domain = category.get('domain')
                    if domain == 'category':
                        cat_name = category.text
                        if cat_name:
                            post['categories'].append(cat_name)
                
                posts.append(post)
        
        return posts
    
    def generate_structured_data(self):
        """Generar datos estructurados para el desarrollo"""
        
        print("Extrayendo productos...")
        products = self.extract_products()
        
        print("Extrayendo páginas...")
        pages = self.extract_pages()
        
        print("Extrayendo posts...")
        posts = self.extract_posts()
        
        # Agrupar productos por tipo/familia
        product_families = {}
        for product in products:
            # Extraer nombre base (sin talla)
            base_name = re.sub(r'\s+Talla\s+\w+', '', product['title'])
            base_name = re.sub(r'\s+\d+$', '', base_name)
            
            if base_name not in product_families:
                product_families[base_name] = []
            product_families[base_name].append(product)
        
        # Generar estructura final
        structured_data = {
            'extraction_date': datetime.now().isoformat(),
            'source_file': self.xml_file,
            'summary': {
                'total_products': len(products),
                'product_families': len(product_families),
                'pages': len(pages),
                'posts': len(posts),
                'unique_categories': len(set(
                    [cat for p in products for cat in p['categories']]
                ))
            },
            'product_families': product_families,
            'all_products': products,
            'pages': pages,
            'posts': posts,
            'content_analysis': {
                'popular_keywords': self._extract_keywords(products + pages + posts),
                'price_ranges': self._analyze_price_ranges(products),
                'common_attributes': self._analyze_attributes(products)
            }
        }
        
        return structured_data
    
    def _extract_keywords(self, items):
        """Extraer palabras clave comunes"""
        all_text = ' '.join([
            item.get('title', '') + ' ' + item.get('description', '') 
            for item in items
        ])
        
        # Palabras clave relevantes para el negocio
        keywords = [
            'buzo', 'polera', 'poleron', 'pantalón', 'chaqueta', 'camiseta',
            'colegio', 'los reyes', 'deportivo', 'uniforme', 'bordado',
            'talla', 'color', 'niño', 'niña', 'juvenil', 'adulto'
        ]
        
        found_keywords = []
        for keyword in keywords:
            if keyword.lower() in all_text.lower():
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _analyze_price_ranges(self, products):
        """Analizar rangos de precios"""
        prices = [p['price'] for p in products if p['price'] > 0]
        
        if not prices:
            return {}
        
        return {
            'min_price': min(prices),
            'max_price': max(prices),
            'avg_price': sum(prices) / len(prices),
            'price_ranges': {
                'economy': len([p for p in prices if p < 10000]),
                'mid_range': len([p for p in prices if 10000 <= p < 20000]),
                'premium': len([p for p in prices if p >= 20000])
            }
        }
    
    def _analyze_attributes(self, products):
        """Analizar atributos comunes"""
        all_attributes = {}
        
        for product in products:
            for attr_name, attr_value in product['attributes'].items():
                if attr_name not in all_attributes:
                    all_attributes[attr_name] = set()
                all_attributes[attr_name].add(attr_value)
        
        # Convertir sets a lists
        return {k: list(v) for k, v in all_attributes.items()}

def main():
    extractor = WordPressExtractor('wordpress export/juliaconfecciones.WordPress.2025-09-12full.xml')
    
    print("Iniciando extraccion de contenido WordPress...")
    structured_data = extractor.generate_structured_data()
    
    # Guardar JSON estructurado
    with open('wordpress_content_structured.json', 'w', encoding='utf-8') as f:
        json.dump(structured_data, f, ensure_ascii=False, indent=2)
    
    print("Extraccion completada!")
    print("Resumen:")
    print(f"   - Productos: {structured_data['summary']['total_products']}")
    print(f"   - Familias de productos: {structured_data['summary']['product_families']}")
    print(f"   - Paginas: {structured_data['summary']['pages']}")
    print(f"   - Posts: {structured_data['summary']['posts']}")
    print(f"   - Categorias unicas: {structured_data['summary']['unique_categories']}")
    
    print("\nArchivos generados:")
    print("   - wordpress_content_structured.json (datos completos)")
    
    return structured_data

if __name__ == "__main__":
    structured_data = main()