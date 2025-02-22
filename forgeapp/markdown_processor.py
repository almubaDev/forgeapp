def process_markdown_section(text):
    """
    Procesa texto markdown y retorna una lista de secciones procesadas
    """
    sections = []
    current_section = []
    current_list = []
    in_list = False
    
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Línea vacía
        if not line:
            if current_list:
                sections.append(('list', current_list))
                current_list = []
                in_list = False
            elif current_section:
                sections.append(('content', '\n'.join(current_section)))
                current_section = []
            i += 1
            continue
        
        # Títulos con #
        if line.startswith('#'):
            if current_list:
                sections.append(('list', current_list))
                current_list = []
                in_list = False
            elif current_section:
                sections.append(('content', '\n'.join(current_section)))
                current_section = []
            
            level = len(line) - len(line.lstrip('#'))
            title = line[level:].strip()
            sections.append(('title', {'text': title, 'level': level}))
            i += 1
            continue
        
        # Títulos con === o ---
        if i > 0 and (line.startswith('===') or line.startswith('---')):
            if current_section:
                title = current_section.pop()
                sections.append(('title', {'text': title, 'level': 1}))
                current_section = []
            i += 1
            continue
        
        # Listas
        if line.lstrip().startswith('•') or line.lstrip().startswith('*'):
            if not in_list and current_section:
                sections.append(('content', '\n'.join(current_section)))
                current_section = []
            
            in_list = True
            item = line.lstrip('•* \t')  # Eliminar viñetas y espacios
            # Manejar texto en negrita
            if '**' in item:
                parts = item.split('**')
                for j in range(len(parts)):
                    if j % 2 == 1:  # Es contenido entre **
                        parts[j] = f'<b>{parts[j]}</b>'
                item = ''.join(parts)
            current_list.append(item)
            i += 1
            continue
        
        # Texto en negrita fuera de listas
        if '**' in line:
            parts = line.split('**')
            for j in range(len(parts)):
                if j % 2 == 1:  # Es contenido entre **
                    parts[j] = f'<b>{parts[j]}</b>'
            line = ''.join(parts)
        
        # Texto normal
        if in_list:
            sections.append(('list', current_list))
            current_list = []
            in_list = False
        current_section.append(line)
        i += 1
    
    # Procesar última sección
    if current_list:
        sections.append(('list', current_list))
    elif current_section:
        sections.append(('content', '\n'.join(current_section)))
    
    return sections
