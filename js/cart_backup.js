// public/js/cart.js - Core Cart Logic
const CART_STORAGE_KEY = 'wcs_cart';

export const getCart = () => {
    try {
        const cart = JSON.parse(localStorage.getItem(CART_STORAGE_KEY) || '[]');
        return Array.isArray(cart) ? cart : [];
    } catch (e) {
        return [];
    }
};

export const saveCart = (cart) => {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
    // Trigger custom event for UI components to listen to
    window.dispatchEvent(new CustomEvent('cartUpdated', { detail: cart }));
};

export const addToCart = (product, qty = 1) => {
    let cart = getCart();
    const existing = cart.find(item => item.product.id === product.id);
    
    if (existing) {
        existing.qty += qty;
    } else {
        cart.push({ product, qty });
    }
    
    saveCart(cart);
};

export const removeFromCart = (productId) => {
    let cart = getCart();
    cart = cart.filter(item => item.product.id !== productId);
    saveCart(cart);
};

export const updateQuantity = (productId, qty) => {
    let cart = getCart();
    const item = cart.find(item => item.product.id === productId);
    if (item) {
        item.qty = Math.max(0, qty);
        if (item.qty === 0) {
            removeFromCart(productId);
        } else {
            saveCart(cart);
        }
    }
};

export const clearCart = () => {
    localStorage.removeItem(CART_STORAGE_KEY);
    window.dispatchEvent(new CustomEvent('cartUpdated', { detail: [] }));
};

window.addToCart = addToCart;
