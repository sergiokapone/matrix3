    document.addEventListener('DOMContentLoaded', function() {
        const triggers = document.querySelectorAll('.tooltip-trigger');
        let currentTooltip = null;
        
        triggers.forEach(trigger => {
            trigger.addEventListener('mouseenter', function(e) {
                // Видаляємо попередню підказку
                if (currentTooltip) {
                    currentTooltip.remove();
                    currentTooltip = null;
                }
                
                const tooltipText = this.getAttribute('data-tooltip');
                if (!tooltipText) return;
                
                // Створюємо нову підказку
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip show';
                tooltip.textContent = tooltipText;
                
                // Додаємо до body
                document.body.appendChild(tooltip);
                currentTooltip = tooltip;
                
                // Позиціонуємо підказку відносно курсора
                const rect = this.getBoundingClientRect();
                const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
                
                // Позиція зверху від елементу
                let left = rect.left + scrollLeft + (rect.width / 2) - (tooltip.offsetWidth / 2);
                let top = rect.top + scrollTop - tooltip.offsetHeight - 10;
                
                // Якщо виходить за верхню межу, показуємо знизу
                if (top < scrollTop + 10) {
                    top = rect.bottom + scrollTop + 10;
                    // Змінюємо стрілочку
                    tooltip.style.setProperty('--arrow-direction', 'up');
                }
                
                // Якщо виходить за ліву межу
                if (left < scrollLeft + 10) {
                    left = scrollLeft + 10;
                }
                
                // Якщо виходить за праву межу
                if (left + tooltip.offsetWidth > scrollLeft + window.innerWidth - 10) {
                    left = scrollLeft + window.innerWidth - tooltip.offsetWidth - 10;
                }
                
                tooltip.style.left = left + 'px';
                tooltip.style.top = top + 'px';
            });
            
            trigger.addEventListener('mouseleave', function() {
                if (currentTooltip) {
                    currentTooltip.classList.remove('show');
                    setTimeout(() => {
                        if (currentTooltip) {
                            currentTooltip.remove();
                            currentTooltip = null;
                        }
                    }, 200);
                }
            });
        });
        
        // Видаляємо підказку при прокрутці або кліку
        window.addEventListener('scroll', function() {
            if (currentTooltip) {
                currentTooltip.remove();
                currentTooltip = null;
            }
        });
        
        document.addEventListener('click', function() {
            if (currentTooltip) {
                currentTooltip.remove();
                currentTooltip = null;
            }
        });
        
        console.log('Tooltip script loaded. Found triggers:', triggers.length);
    });