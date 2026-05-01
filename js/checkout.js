const initiateCheckout = async (email = '') => {
    const cart = typeof getCart === 'function' ? getCart() : (window.getCart ? window.getCart() : []);
    
    if (cart.length === 0) {
        alert('Dein Warenkorb ist leer.');
        return;
    }

    try {
        const response = await fetch('/api/create-checkout-session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ cart, email }),
        });

        const session = await response.json();

        if (session.url) {
            window.location.href = session.url;
        } else {
            console.error('Checkout Error:', session.error);
            alert('Fehler beim Starten des Checkouts: ' + (session.error || 'Unbekannter Fehler'));
        }
    } catch (err) {
        console.error('Fetch Error:', err);
        alert('Netzwerkfehler beim Starten des Checkouts.');
    }
};

// Bind to checkout buttons if present
document.addEventListener('DOMContentLoaded', () => {
    const checkoutBtn = document.querySelector('.js-btn-checkout');
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const emailInput = document.getElementById('checkout-email');
            initiateCheckout(emailInput ? emailInput.value : '');
        });
    }
});

window.initiateCheckout = initiateCheckout;
