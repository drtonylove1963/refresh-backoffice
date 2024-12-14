const validators = {
    name: (value) => {
        return value.length >= 2;
    },
    phone: (value) => {
        return /^\d{10,}$/.test(value.replace(/\D/g, ''));
    },
    email: (value) => {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
    },
    date: (value) => {
        const date = new Date(value);
        const today = new Date();
        return date >= today;
    }
};

function validateStep(step) {
    const fields = document.querySelectorAll(`[data-step="${step}"] input[required]`);
    let isValid = true;

    fields.forEach(field => {
        const value = field.value.trim();
        const type = field.getAttribute('data-validate') || field.type;
        
        if (validators[type] && !validators[type](value)) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });

    return isValid;
}
