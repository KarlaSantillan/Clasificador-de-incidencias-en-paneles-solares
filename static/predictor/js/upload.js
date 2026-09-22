(() => {
    'use strict';

    document.documentElement.classList.add('js');
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

    const initializeNavigation = () => {
        const toggle = document.querySelector('.nav-toggle');
        const navigation = document.querySelector('#primary-navigation');
        if (!toggle || !navigation) return;

        const closeMenu = () => {
            toggle.setAttribute('aria-expanded', 'false');
            toggle.setAttribute('aria-label', 'Abrir menú');
            navigation.classList.remove('is-open');
        };

        toggle.addEventListener('click', () => {
            const willOpen = toggle.getAttribute('aria-expanded') !== 'true';
            toggle.setAttribute('aria-expanded', String(willOpen));
            toggle.setAttribute('aria-label', willOpen ? 'Cerrar menú' : 'Abrir menú');
            navigation.classList.toggle('is-open', willOpen);
        });

        navigation.addEventListener('click', (event) => {
            if (event.target.closest('a')) closeMenu();
        });

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                closeMenu();
                toggle.focus();
            }
        });

        document.addEventListener('click', (event) => {
            if (!navigation.contains(event.target) && !toggle.contains(event.target)) closeMenu();
        });

        window.addEventListener('resize', () => {
            if (window.innerWidth > 760) closeMenu();
        });
    };

    const initializeRevealAnimations = () => {
        const elements = [...document.querySelectorAll('[data-reveal]')];
        if (!elements.length) return;

        if (reducedMotion.matches || !('IntersectionObserver' in window)) {
            elements.forEach((element) => element.classList.add('is-visible'));
            return;
        }

        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target);
            });
        }, { threshold: 0.12, rootMargin: '0px 0px -30px' });

        elements.forEach((element) => observer.observe(element));
    };

    const initializeProbabilityBars = () => {
        const meters = [...document.querySelectorAll('.probability-meter[data-probability]')];
        if (!meters.length) return;

        const safeTarget = (meter) => {
            const parsed = Number.parseFloat(meter.dataset.probability);
            return Number.isFinite(parsed) ? Math.min(Math.max(parsed, 0), 100) : 0;
        };

        const animate = (meter) => {
            const target = safeTarget(meter);
            if (reducedMotion.matches) {
                meter.value = target;
                return;
            }

            meter.value = 0;
            const startedAt = performance.now();
            const duration = 480;
            const frame = (now) => {
                const progress = Math.min((now - startedAt) / duration, 1);
                const eased = 1 - Math.pow(1 - progress, 3);
                meter.value = target * eased;
                if (progress < 1) window.requestAnimationFrame(frame);
            };
            window.requestAnimationFrame(frame);
        };

        if (!('IntersectionObserver' in window)) {
            meters.forEach(animate);
            return;
        }

        meters.forEach((meter) => { meter.value = reducedMotion.matches ? safeTarget(meter) : 0; });
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                animate(entry.target);
                observer.unobserve(entry.target);
            });
        }, { threshold: 0.35 });
        meters.forEach((meter) => observer.observe(meter));
    };

    const initializeUpload = () => {
        const form = document.querySelector('#analysis-form');
        if (!form) return;

        const input = form.querySelector('#id_image');
        const dropZone = form.querySelector('#drop-zone');
        const emptyState = form.querySelector('.drop-zone__label');
        const selectedState = form.querySelector('#selected-file');
        const preview = form.querySelector('#image-preview');
        const fileName = form.querySelector('#file-name');
        const fileSize = form.querySelector('#file-size');
        const removeButton = form.querySelector('#remove-file');
        const submitButton = form.querySelector('#submit-button');
        const clientError = form.querySelector('#client-file-error');
        const processingStatus = form.querySelector('#processing-status');
        const uploadPanel = form.closest('.upload-panel');
        if (!input || !dropZone || !emptyState || !selectedState || !preview || !fileName || !fileSize || !removeButton || !submitButton || !clientError || !processingStatus || !uploadPanel) return;

        const maxBytes = 10 * 1024 * 1024;
        const allowedExtensions = new Set(['jpg', 'jpeg', 'png', 'webp']);
        const allowedTypes = new Set(['image/jpeg', 'image/png', 'image/webp']);
        let previewUrl = null;
        let selectedFile = null;

        const extensionOf = (name) => name.includes('.') ? name.split('.').pop().toLowerCase() : '';
        const readableSize = (bytes) => bytes >= 1024 * 1024
            ? `${(bytes / (1024 * 1024)).toFixed(2)} MB`
            : `${Math.max(1, Math.round(bytes / 1024))} KB`;

        const showClientError = (message = '') => {
            clientError.textContent = message;
            clientError.hidden = !message;
            dropZone.classList.toggle('has-error', Boolean(message));
        };

        const validateCandidate = (file) => {
            if (!file || file.size === 0) return 'El archivo está vacío.';
            if (file.size > maxBytes) return 'La imagen supera el tamaño máximo permitido de 10 MB.';
            if (!allowedExtensions.has(extensionOf(file.name))) return 'Selecciona un archivo JPG, JPEG, PNG o WEBP.';
            if (file.type && !allowedTypes.has(file.type)) return 'El tipo de archivo seleccionado no está permitido.';
            return '';
        };

        const clearSelection = ({ clearInput = true } = {}) => {
            if (previewUrl) URL.revokeObjectURL(previewUrl);
            previewUrl = null;
            selectedFile = null;
            if (clearInput) input.value = '';
            preview.removeAttribute('src');
            fileName.textContent = '';
            fileSize.textContent = '';
            selectedState.hidden = true;
            emptyState.hidden = false;
            submitButton.disabled = true;
        };

        const showSelection = (file) => {
            const validationMessage = validateCandidate(file);
            showClientError(validationMessage);
            if (validationMessage) {
                clearSelection();
                return;
            }

            if (previewUrl) URL.revokeObjectURL(previewUrl);
            selectedFile = file;
            previewUrl = URL.createObjectURL(file);
            preview.src = previewUrl;
            fileName.textContent = file.name;
            fileSize.textContent = readableSize(file.size);
            emptyState.hidden = true;
            selectedState.hidden = false;
            submitButton.disabled = false;
        };

        input.addEventListener('change', () => showSelection(input.files[0]));
        removeButton.addEventListener('click', () => {
            showClientError();
            clearSelection();
            input.focus();
        });

        ['dragenter', 'dragover'].forEach((eventName) => {
            dropZone.addEventListener(eventName, (event) => {
                event.preventDefault();
                if (!form.dataset.submitting) dropZone.classList.add('is-dragging');
            });
        });

        ['dragleave', 'drop'].forEach((eventName) => {
            dropZone.addEventListener(eventName, (event) => {
                event.preventDefault();
                dropZone.classList.remove('is-dragging');
            });
        });

        dropZone.addEventListener('drop', (event) => {
            if (form.dataset.submitting) return;
            const file = event.dataTransfer.files[0];
            if (!file) return;
            try {
                const transfer = new DataTransfer();
                transfer.items.add(file);
                input.files = transfer.files;
            } catch (error) {
                showClientError('No fue posible añadir el archivo arrastrado. Selecciónalo manualmente.');
                return;
            }
            showSelection(file);
        });

        form.addEventListener('submit', (event) => {
            if (form.dataset.submitting || !selectedFile) {
                event.preventDefault();
                return;
            }
            form.dataset.submitting = 'true';
            uploadPanel.classList.add('is-processing');
            submitButton.disabled = true;
            removeButton.disabled = true;
            submitButton.querySelector('.button-label').hidden = true;
            submitButton.querySelector('.processing-label').hidden = false;
            submitButton.setAttribute('aria-busy', 'true');
            processingStatus.hidden = false;
        });

        window.addEventListener('pageshow', (event) => {
            if (!event.persisted) return;
            delete form.dataset.submitting;
            uploadPanel.classList.remove('is-processing');
            removeButton.disabled = false;
            submitButton.querySelector('.button-label').hidden = false;
            submitButton.querySelector('.processing-label').hidden = true;
            submitButton.removeAttribute('aria-busy');
            processingStatus.hidden = true;
            submitButton.disabled = !selectedFile;
        });
    };

    initializeNavigation();
    initializeRevealAnimations();
    initializeProbabilityBars();
    initializeUpload();
})();
