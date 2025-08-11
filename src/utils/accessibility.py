from nicegui import ui
from typing import Dict, List, Optional

class AccessibilityHelper:
    """Utility class for accessibility enhancements"""
    
    @staticmethod
    def add_keyboard_navigation():
        """Add global keyboard navigation support"""
        keyboard_js = '''
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Skip to main content functionality
            const skipLink = document.createElement('a');
            skipLink.href = '#main-content';
            skipLink.textContent = 'Skip to main content';
            skipLink.className = 'sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-emerald-600 text-white px-4 py-2 rounded z-50';
            skipLink.addEventListener('focus', function() {
                this.classList.remove('sr-only');
            });
            skipLink.addEventListener('blur', function() {
                this.classList.add('sr-only');
            });
            document.body.insertBefore(skipLink, document.body.firstChild);
            
            // Enhanced focus management
            let lastFocusedElement = null;
            
            document.addEventListener('keydown', function(e) {
                // Track last focused element for modal management
                if (e.target !== document.body) {
                    lastFocusedElement = e.target;
                }
                
                // Escape key to close modals/popups
                if (e.key === 'Escape') {
                    const modals = document.querySelectorAll('[role="dialog"], .modal, .popup');
                    if (modals.length > 0) {
                        const topModal = modals[modals.length - 1];
                        const closeBtn = topModal.querySelector('button[aria-label*="close"], .close-btn');
                        if (closeBtn) {
                            closeBtn.click();
                        }
                        e.preventDefault();
                    }
                }
                
                // Arrow key navigation for card grids
                if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                    const focusedCard = document.activeElement.closest('[role="article"]');
                    if (focusedCard) {
                        const allCards = Array.from(document.querySelectorAll('[role="article"]'));
                        const currentIndex = allCards.indexOf(focusedCard);
                        let nextIndex = -1;
                        
                        switch (e.key) {
                            case 'ArrowRight':
                                nextIndex = currentIndex + 1;
                                break;
                            case 'ArrowLeft':
                                nextIndex = currentIndex - 1;
                                break;
                            case 'ArrowDown':
                                // Assume 2-column layout on desktop, 1-column on mobile
                                const columnsPerRow = window.innerWidth >= 768 ? 2 : 1;
                                nextIndex = currentIndex + columnsPerRow;
                                break;
                            case 'ArrowUp':
                                const columnsPerRowUp = window.innerWidth >= 768 ? 2 : 1;
                                nextIndex = currentIndex - columnsPerRowUp;
                                break;
                        }
                        
                        if (nextIndex >= 0 && nextIndex < allCards.length) {
                            allCards[nextIndex].focus();
                            e.preventDefault();
                        }
                    }
                }
                
                // Enter/Space key activation for custom interactive elements
                if ((e.key === 'Enter' || e.key === ' ') && e.target.hasAttribute('data-clickable')) {
                    e.target.click();
                    e.preventDefault();
                }
            });
            
            // Announce dynamic content changes to screen readers
            function announceToScreenReader(message) {
                const announcement = document.createElement('div');
                announcement.setAttribute('aria-live', 'polite');
                announcement.setAttribute('aria-atomic', 'true');
                announcement.className = 'sr-only';
                announcement.textContent = message;
                document.body.appendChild(announcement);
                
                setTimeout(() => {
                    document.body.removeChild(announcement);
                }, 1000);
            }
            
            // Monitor for content changes and announce them
            const contentObserver = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'childList') {
                        mutation.addedNodes.forEach(function(node) {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                // Announce when recipes are loaded
                                if (node.querySelector('[role="article"]')) {
                                    const recipeCount = node.querySelectorAll('[role="article"]').length;
                                    announceToScreenReader(`${recipeCount} recipes loaded`);
                                }
                                
                                // Announce loading states
                                if (node.querySelector('.loading-shimmer')) {
                                    announceToScreenReader('Content is loading');
                                }
                                
                                // Announce error states
                                if (node.querySelector('[role="alert"]')) {
                                    const errorMsg = node.querySelector('[role="alert"]').textContent;
                                    announceToScreenReader(`Error: ${errorMsg}`);
                                }
                            }
                        });
                    }
                });
            });
            
            contentObserver.observe(document.body, {
                childList: true,
                subtree: true
            });
            
            // Improve focus visibility for custom elements
            const style = document.createElement('style');
            style.textContent = `
                [tabindex]:focus,
                button:focus,
                input:focus,
                textarea:focus,
                select:focus {
                    outline: 2px solid #10b981 !important;
                    outline-offset: 2px !important;
                }
                
                .sr-only {
                    position: absolute !important;
                    width: 1px !important;
                    height: 1px !important;
                    padding: 0 !important;
                    margin: -1px !important;
                    overflow: hidden !important;
                    clip: rect(0, 0, 0, 0) !important;
                    white-space: nowrap !important;
                    border: 0 !important;
                }
                
                .focus\\:not-sr-only:focus {
                    position: static !important;
                    width: auto !important;
                    height: auto !important;
                    padding: inherit !important;
                    margin: inherit !important;
                    overflow: visible !important;
                    clip: auto !important;
                    white-space: normal !important;
                }
            `;
            document.head.appendChild(style);
        });
        </script>
        '''
        ui.add_head_html(keyboard_js)
    
    @staticmethod
    def create_accessible_button(
        text: str,
        on_click,
        theme: Dict[str, str],
        button_type: str = "primary",
        aria_label: Optional[str] = None,
        is_loading: bool = False
    ):
        """Create an accessible button with proper ARIA attributes"""
        button_classes = {
            "primary": theme["button_primary"],
            "secondary": theme["button_secondary"], 
            "ghost": theme["button_ghost"]
        }
        
        classes = f'{button_classes.get(button_type, button_classes["primary"])} touch-target focus-visible button-interactive'
        
        props = f'role="button" tabindex="0"'
        if aria_label:
            props += f' aria-label="{aria_label}"'
        if is_loading:
            props += ' aria-disabled="true" aria-busy="true"'
        
        return ui.button(text, on_click=on_click if not is_loading else None).classes(classes).props(props)
    
    @staticmethod
    def create_accessible_form_field(
        field_type: str,
        label: str,
        theme: Dict[str, str],
        placeholder: Optional[str] = None,
        required: bool = False,
        aria_describedby: Optional[str] = None,
        **kwargs
    ):
        """Create accessible form fields with proper labels and ARIA attributes"""
        field_id = f"field-{label.lower().replace(' ', '-')}"
        
        # Create label
        label_html = f'<label for="{field_id}" class="block text-sm font-medium {theme["text_secondary"]} mb-2'
        if required:
            label_html += '">'
            label_html += f'{label} <span aria-label="required" class="text-red-500">*</span>'
        else:
            label_html += f'">{label}'
        label_html += '</label>'
        
        ui.html(label_html)
        
        # Create field
        field_props = f'id="{field_id}"'
        if required:
            field_props += ' required aria-required="true"'
        if aria_describedby:
            field_props += f' aria-describedby="{aria_describedby}"'
        
        classes = f'{theme["input_bg"]} w-full rounded-xl border-2 p-3 touch-target focus-visible'
        
        if field_type == "textarea":
            return ui.textarea(
                placeholder=placeholder,
                **kwargs
            ).classes(classes).props(field_props).style('font-size: 16px;')
        else:
            return ui.input(
                placeholder=placeholder,
                **kwargs
            ).classes(classes).props(field_props).style('font-size: 16px;')
    
    @staticmethod
    def announce_live_update(message: str, priority: str = "polite"):
        """Announce dynamic updates to screen readers"""
        announce_js = f'''
        <script>
        (function() {{
            const announcement = document.createElement('div');
            announcement.setAttribute('aria-live', '{priority}');
            announcement.setAttribute('aria-atomic', 'true');
            announcement.className = 'sr-only';
            announcement.textContent = '{message}';
            document.body.appendChild(announcement);
            
            setTimeout(function() {{
                if (document.body.contains(announcement)) {{
                    document.body.removeChild(announcement);
                }}
            }}, 1000);
        }})();
        </script>
        '''
        ui.add_head_html(announce_js)

def add_accessibility_enhancements():
    """Add comprehensive accessibility enhancements to the application"""
    AccessibilityHelper.add_keyboard_navigation()
    
    # Add main landmark
    ui.add_head_html('''
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        // Find main content area and add proper landmark
        const mainContent = document.querySelector('.flex-1') || document.querySelector('main') || document.body;
        if (mainContent && !mainContent.hasAttribute('id')) {
            mainContent.setAttribute('id', 'main-content');
            mainContent.setAttribute('role', 'main');
        }
    });
    </script>
    ''')