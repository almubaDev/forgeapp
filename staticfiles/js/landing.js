// Inicialización de partículas
function initParticles() {
    if (typeof particlesJS !== 'undefined') {
        particlesJS('particles-js', {
            particles: {
                number: {
                    value: 80,
                    density: {
                        enable: true,
                        value_area: 800
                    }
                },
                color: {
                    value: '#00B4D8'
                },
                shape: {
                    type: 'circle'
                },
                opacity: {
                    value: 0.5,
                    random: true,
                    anim: {
                        enable: true,
                        speed: 1,
                        opacity_min: 0.1,
                        sync: false
                    }
                },
                size: {
                    value: 3,
                    random: true,
                    anim: {
                        enable: true,
                        speed: 2,
                        size_min: 0.1,
                        sync: false
                    }
                },
                line_linked: {
                    enable: true,
                    distance: 150,
                    color: '#00B4D8',
                    opacity: 0.2,
                    width: 1
                },
                move: {
                    enable: true,
                    speed: 2,
                    direction: 'none',
                    random: false,
                    straight: false,
                    out_mode: 'out',
                    bounce: false,
                    attract: {
                        enable: true,
                        rotateX: 600,
                        rotateY: 1200
                    }
                }
            },
            interactivity: {
                detect_on: 'canvas',
                events: {
                    onhover: {
                        enable: true,
                        mode: 'repulse'
                    },
                    onclick: {
                        enable: true,
                        mode: 'push'
                    },
                    resize: true
                },
                modes: {
                    repulse: {
                        distance: 100,
                        duration: 0.4
                    },
                    push: {
                        particles_nb: 4
                    }
                }
            },
            retina_detect: true
        });
    }
}

// Animaciones con GSAP
function initGSAPAnimations() {
    gsap.registerPlugin(ScrollTrigger);

    // Animación del logo al hacer scroll
    gsap.to('.logo-container', {
        scrollTrigger: {
            trigger: '.hero',
            start: 'top top',
            end: 'bottom top',
            scrub: 1
        },
        y: 50,
        scale: 0.8,
        opacity: 0.8
    });

    // Animación de las cards
    const cards = gsap.utils.toArray('.card');
    cards.forEach((card, i) => {
        gsap.from(card, {
            scrollTrigger: {
                trigger: card,
                start: 'top bottom-=100',
                toggleActions: 'play none none reverse'
            },
            y: 100,
            opacity: 0,
            duration: 0.8,
            delay: i * 0.2
        });
    });
}

// Efecto para las líneas de circuito
function createCircuitLines() {
    const containers = document.querySelectorAll('.circuit-lines');
    
    containers.forEach(container => {
        container.innerHTML = '';
        
        for (let i = 0; i < 8; i++) {
            const line = document.createElement('div');
            line.className = 'circuit-line';
            
            line.style.cssText = `
                position: absolute;
                width: ${Math.random() * 200 + 100}px;
                height: 1px;
                top: ${Math.random() * 100}%;
                left: ${Math.random() * 100}%;
                background: linear-gradient(90deg, transparent, var(--primary-color), transparent);
                opacity: 0.3;
                transform: rotate(${Math.random() * 360}deg);
            `;
            
            line.animate([
                { opacity: 0.1 },
                { opacity: 0.3 },
                { opacity: 0.1 }
            ], {
                duration: 2000 + Math.random() * 3000,
                iterations: Infinity,
                delay: Math.random() * 2000
            });
            
            container.appendChild(line);
        }
    });
}

// Navegación Móvil
function initMobileMenu() {
    const menuButton = document.querySelector('.mobile-menu-button');
    const navLinks = document.querySelector('.nav-links');
    
    if (menuButton && navLinks) {
        menuButton.addEventListener('click', () => {
            navLinks.classList.toggle('show');
            menuButton.textContent = navLinks.classList.contains('show') ? '✕' : '☰';
        });
        
        document.querySelectorAll('.nav-links a').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('show');
                menuButton.textContent = '☰';
            });
        });
    }
}

// Scroll Suave
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            
            if (target) {
                const headerOffset = 80;
                const elementPosition = target.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                
                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Manejo del formulario de contacto con pasos
function initContactForm() {
    const form = document.getElementById('contact-form');
    if (!form) return;

    const step1 = document.getElementById('step-1');
    const step2 = document.getElementById('step-2');
    const nextBtn = document.getElementById('next-step');
    const prevBtn = document.getElementById('prev-step');
    const submitBtn = document.getElementById('submit-btn');
    const dateInput = document.getElementById('appointment_date');
    const timeInput = document.getElementById('appointment_time');
    const noSlotsMessage = document.getElementById('no-slots-message');
    const stepItems = document.querySelectorAll('.step-item');
    const calendarDays = document.getElementById('calendar-days');
    const calendarMonthYear = document.getElementById('calendar-month-year');
    const prevMonthBtn = document.getElementById('prev-month');
    const nextMonthBtn = document.getElementById('next-month');
    const timeSlotsContainer = document.getElementById('time-slots-container');
    const timeSlotsGrid = document.getElementById('time-slots');
    const selectedDateDisplay = document.getElementById('selected-date-display');

    // Estado del calendario
    let currentDate = new Date();
    let currentMonth = currentDate.getMonth();
    let currentYear = currentDate.getFullYear();
    let selectedDate = null;
    let selectedTime = null;

    const monthNames = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];

    // Función para renderizar el calendario
    function renderCalendar() {
        const firstDay = new Date(currentYear, currentMonth, 1);
        const lastDay = new Date(currentYear, currentMonth + 1, 0);
        const startingDay = (firstDay.getDay() + 6) % 7; // Ajustar para que lunes sea 0
        const totalDays = lastDay.getDate();

        calendarMonthYear.textContent = `${monthNames[currentMonth]} ${currentYear}`;
        calendarDays.innerHTML = '';

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        // Días vacíos al inicio
        for (let i = 0; i < startingDay; i++) {
            const emptyDay = document.createElement('div');
            emptyDay.className = 'calendar-day empty';
            calendarDays.appendChild(emptyDay);
        }

        // Días del mes
        for (let day = 1; day <= totalDays; day++) {
            const dayElement = document.createElement('div');
            dayElement.className = 'calendar-day';
            dayElement.textContent = day;

            const dayDate = new Date(currentYear, currentMonth, day);
            dayDate.setHours(0, 0, 0, 0);

            // Deshabilitar días pasados y el día actual
            if (dayDate <= today) {
                dayElement.classList.add('disabled');
            } else {
                // Marcar día de hoy (no seleccionable pero visible)
                if (dayDate.getTime() === today.getTime()) {
                    dayElement.classList.add('today');
                }

                // Marcar día seleccionado
                if (selectedDate && dayDate.getTime() === selectedDate.getTime()) {
                    dayElement.classList.add('selected');
                }

                // Evento click
                dayElement.addEventListener('click', () => selectDay(dayDate, day));
            }

            calendarDays.appendChild(dayElement);
        }
    }

    // Función para seleccionar un día
    function selectDay(date, dayNum) {
        selectedDate = date;
        selectedTime = null;
        timeInput.value = '';
        updateSubmitButton();

        // Actualizar visualización
        document.querySelectorAll('.calendar-day').forEach(d => d.classList.remove('selected'));
        event.target.classList.add('selected');

        // Formatear fecha para mostrar
        const formattedDate = date.toLocaleDateString('es-CL', {
            weekday: 'long',
            day: 'numeric',
            month: 'long'
        });
        selectedDateDisplay.textContent = formattedDate;

        // Guardar en input hidden
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        dateInput.value = `${year}-${month}-${day}`;

        // Cargar horarios disponibles
        loadTimeSlots(dateInput.value);
    }

    // Función para cargar horarios disponibles
    function loadTimeSlots(dateStr) {
        timeSlotsContainer.style.display = 'block';
        timeSlotsGrid.innerHTML = '<div class="time-slots-loading">Cargando horarios</div>';
        noSlotsMessage.style.display = 'none';

        fetch(`/agenda/available-slots/?date=${dateStr}`)
            .then(response => response.json())
            .then(data => {
                timeSlotsGrid.innerHTML = '';

                if (data.slots && data.slots.length > 0) {
                    data.slots.forEach(slot => {
                        const slotElement = document.createElement('div');
                        slotElement.className = 'time-slot';
                        slotElement.textContent = slot.time;
                        slotElement.dataset.time = slot.time;

                        slotElement.addEventListener('click', () => selectTimeSlot(slotElement, slot.time));

                        timeSlotsGrid.appendChild(slotElement);
                    });
                    noSlotsMessage.style.display = 'none';
                } else {
                    timeSlotsGrid.innerHTML = '';
                    noSlotsMessage.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error cargando horarios:', error);
                timeSlotsGrid.innerHTML = '<p style="color: #fca5a5; text-align: center;">Error al cargar horarios</p>';
            });
    }

    // Función para seleccionar horario
    function selectTimeSlot(element, time) {
        selectedTime = time;
        timeInput.value = time;

        // Actualizar visualización
        document.querySelectorAll('.time-slot').forEach(s => s.classList.remove('selected'));
        element.classList.add('selected');

        updateSubmitButton();
    }

    // Función para actualizar estado del botón submit
    function updateSubmitButton() {
        submitBtn.disabled = !(selectedDate && selectedTime);
    }

    // Navegación del calendario
    prevMonthBtn.addEventListener('click', () => {
        const today = new Date();
        const minMonth = today.getMonth();
        const minYear = today.getFullYear();

        // No permitir ir a meses anteriores al actual
        if (currentYear > minYear || (currentYear === minYear && currentMonth > minMonth)) {
            currentMonth--;
            if (currentMonth < 0) {
                currentMonth = 11;
                currentYear--;
            }
            renderCalendar();
        }
    });

    nextMonthBtn.addEventListener('click', () => {
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }
        renderCalendar();
    });

    // Función para validar email
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // Función para mostrar error en campo
    function showFieldError(field, message) {
        // Remover error previo si existe
        const existingError = field.parentElement.querySelector('.field-error');
        if (existingError) existingError.remove();

        // Crear mensaje de error
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.style.cssText = 'color: #fca5a5; font-size: 0.85rem; margin-top: 0.5rem;';
        errorDiv.textContent = message;
        field.parentElement.appendChild(errorDiv);

        // Marcar campo con error
        field.style.borderColor = '#ef4444';
    }

    // Función para limpiar error de campo
    function clearFieldError(field) {
        const existingError = field.parentElement.querySelector('.field-error');
        if (existingError) existingError.remove();
        field.style.borderColor = '';
    }

    // Navegación entre pasos
    nextBtn.addEventListener('click', function() {
        // Validar campos del paso 1
        const name = document.getElementById('nombre');
        const email = document.getElementById('email');
        const message = document.getElementById('mensaje');

        // Limpiar errores previos
        clearFieldError(name);
        clearFieldError(email);
        clearFieldError(message);

        let hasError = false;

        // Validar nombre
        if (!name.value.trim()) {
            showFieldError(name, 'Por favor ingresa tu nombre');
            hasError = true;
        }

        // Validar email - formato
        if (!email.value.trim()) {
            showFieldError(email, 'Por favor ingresa tu correo electrónico');
            hasError = true;
        } else if (!isValidEmail(email.value.trim())) {
            showFieldError(email, 'Por favor ingresa un correo electrónico válido (ej: nombre@dominio.com)');
            hasError = true;
        }

        // Validar mensaje
        if (!message.value.trim()) {
            showFieldError(message, 'Por favor cuéntanos sobre tu proyecto');
            hasError = true;
        }

        if (hasError) {
            return;
        }

        // Ir al paso 2
        step1.classList.remove('active');
        step2.classList.add('active');
        stepItems[0].classList.remove('active');
        stepItems[0].classList.add('completed');
        stepItems[1].classList.add('active');

        // Renderizar calendario
        renderCalendar();
    });

    prevBtn.addEventListener('click', function() {
        step2.classList.remove('active');
        step1.classList.add('active');
        stepItems[1].classList.remove('active');
        stepItems[0].classList.remove('completed');
        stepItems[0].classList.add('active');
    });

    // Envío del formulario
    form.addEventListener('submit', function(e) {
        e.preventDefault();

        if (!selectedDate || !selectedTime) {
            // Mostrar mensaje de error inline en lugar de alert
            noSlotsMessage.textContent = 'Por favor selecciona fecha y hora para la reunión';
            noSlotsMessage.style.display = 'block';
            timeSlotsContainer.style.display = 'block';
            return;
        }

        const formData = new FormData(form);
        const formContainer = form.parentElement;
        const originalText = submitBtn.textContent;

        submitBtn.textContent = 'Enviando...';
        submitBtn.disabled = true;

        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => {
            return response.json().then(data => {
                if (!response.ok) {
                    throw new Error(data.error || 'Error al enviar');
                }
                return data;
            });
        })
        .then(data => {
            // Obtener fecha y hora para mostrar en el mensaje
            const formattedDate = selectedDate.toLocaleDateString('es-CL', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });

            // Reemplazar formulario con mensaje de éxito
            formContainer.innerHTML = `
                <div class="success-message" style="text-align: center; padding: 3rem 2rem;">
                    <div style="width: 80px; height: 80px; margin: 0 auto 1.5rem; background: linear-gradient(135deg, #10B981, #059669); border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                    </div>
                    <h3 style="font-size: 1.5rem; font-weight: 700; color: #10B981; margin-bottom: 1rem;">¡Reunión Agendada!</h3>
                    <p style="color: rgba(255,255,255,0.8); font-size: 1.1rem; line-height: 1.6; margin-bottom: 0.5rem;">
                        Tu reunión ha sido programada para:
                    </p>
                    <p style="color: #10B981; font-size: 1.2rem; font-weight: 600;">
                        ${formattedDate} a las ${selectedTime} hrs
                    </p>
                    <p style="color: rgba(255,255,255,0.6); font-size: 0.95rem; margin-top: 1rem;">
                        Te enviaremos el link de la reunión a tu correo.
                    </p>
                </div>
            `;
        })
        .catch(error => {
            console.error('Error:', error);
            submitBtn.textContent = error.message || 'Error al enviar';
            submitBtn.style.background = 'linear-gradient(135deg, #EF4444, #DC2626)';
            setTimeout(() => {
                submitBtn.textContent = originalText;
                submitBtn.style.background = '';
                submitBtn.disabled = false;
            }, 3000);
        });
    });
}

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    initParticles();
    initGSAPAnimations();
    createCircuitLines();
    initMobileMenu();
    initSmoothScroll();
    initContactForm();
});

// Optimización para resize
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        createCircuitLines();
    }, 250);
});
