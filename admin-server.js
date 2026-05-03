const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { exec } = require('child_process');
require('dotenv').config();
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname))); // Serve the entire project for preview

const DB_PATH = path.join(__dirname, 'data', 'database.json');
const ORDERS_PATH = path.join(__dirname, 'data', 'orders.json');

// Define storage for images
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        const nation = req.body.nation || 'general';
        const dir = path.join(__dirname, 'images', nation);
        if (!fs.existsSync(dir)){
            fs.mkdirSync(dir, { recursive: true });
        }
        cb(null, dir);
    },
    filename: function (req, file, cb) {
        // Prevent overwriting by appending timestamp if needed, or just use original name
        cb(null, file.originalname);
    }
});
const upload = multer({ storage: storage });

// Create database if not exists
if (!fs.existsSync(DB_PATH)) {
    fs.writeFileSync(DB_PATH, JSON.stringify([]));
}

// Helpers for Products
const readDB = () => JSON.parse(fs.readFileSync(DB_PATH, 'utf-8'));
const writeDB = (data) => fs.writeFileSync(DB_PATH, JSON.stringify(data, null, 4));

// Helpers for Orders
const readOrders = () => {
    if (!fs.existsSync(ORDERS_PATH)) return [];
    return JSON.parse(fs.readFileSync(ORDERS_PATH, 'utf-8'));
};
const writeOrders = (data) => fs.writeFileSync(ORDERS_PATH, JSON.stringify(data, null, 4));

// API: Get all products
app.get('/api/products', (req, res) => {
    try {
        const products = readDB();
        res.json(products);
    } catch (err) {
        res.status(500).json({ error: 'Failed to read database' });
    }
});

// API: Upload an image
app.post('/api/upload', upload.any(), (req, res) => {
    const file = req.files ? req.files.find(f => f.fieldname === 'image') : null;
    if (!file) {
        console.error('Upload Error: No file with fieldname "image" found. Received fields:', req.files ? req.files.map(f => f.fieldname) : 'none');
        return res.status(400).json({ error: 'No file uploaded or wrong fieldname' });
    }
    const nation = req.body.nation || 'general';
    const imagePath = `images/${nation}/${file.filename}`;
    res.json({ imagePath });
});

// API: Bulk upload images
app.post('/api/bulk-upload', upload.any(), (req, res) => {
    const items = req.files ? req.files.filter(f => f.fieldname === 'images') : [];
    if (items.length === 0) {
        console.error('Bulk Upload Error: No files with fieldname "images" found. Received fields:', req.files ? req.files.map(f => f.fieldname) : 'none');
        return res.status(400).json({ error: 'No files uploaded' });
    }
    const nation = req.body.nation || 'general';
    const fileInfos = items.map(file => ({
        originalName: file.originalname,
        imagePath: `images/${nation}/${file.filename}`
    }));
    res.json({ files: fileInfos });
});

// API: Add or Update a product
app.post('/api/products', (req, res) => {
    try {
        const newProduct = req.body;
        if (!newProduct.id) {
            return res.status(400).json({ error: 'Product ID is required' });
        }
        
        let products = readDB();
        const index = products.findIndex(p => p.id === newProduct.id);
        
        if (index >= 0) {
            products[index] = newProduct; // Update
        } else {
            products.push(newProduct); // Create
        }
        
        writeDB(products);
        res.json({ success: true, product: newProduct });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// API: Get all orders
app.get('/api/orders', (req, res) => {
    try {
        res.json(readOrders());
    } catch (err) {
        res.status(500).json({ error: 'Failed to read orders' });
    }
});

// API: Update order status
app.put('/api/orders/:id', (req, res) => {
    try {
        const { id } = req.params;
        const { status } = req.body;
        let orders = readOrders();
        const index = orders.findIndex(o => o.id === id);
        if (index >= 0) {
            orders[index].status = status;
            writeOrders(orders);
            res.json({ success: true, order: orders[index] });
        } else {
            res.status(404).json({ error: 'Order not found' });
        }
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// API: Delete a product
app.delete('/api/products/:id', (req, res) => {
    try {
        let products = readDB();
        products = products.filter(p => p.id !== req.params.id);
        writeDB(products);
        res.json({ success: true });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// API: Create Stripe Checkout Session
app.post('/api/create-checkout-session', async (req, res) => {
    try {
        const { cart, email, customerInfo } = req.body;

        if (!cart || cart.length === 0) {
            return res.status(400).json({ error: 'Cart is empty' });
        }

        const line_items = cart.map(item => {
            const p = item.product;
            const priceInCents = Math.round(p.price * 100);
            
            return {
                price_data: {
                    currency: 'eur',
                    product_data: {
                        name: p.name,
                        images: [p.image.startsWith('http') ? p.image : `https://${req.get('host')}/${p.image}`],
                    },
                    unit_amount: priceInCents,
                },
                quantity: item.qty,
            };
        });

        const session = await stripe.checkout.sessions.create({
            payment_method_types: ['card'],
            line_items: line_items,
            mode: 'payment',
            customer_email: email || undefined,
            success_url: `${req.protocol}://${req.get('host')}/success.html?session_id={CHECKOUT_SESSION_ID}`,
            cancel_url: `${req.protocol}://${req.get('host')}/cancel.html`,
            shipping_address_collection: {
                allowed_countries: ['DE', 'AT', 'CH', 'TR', 'GB', 'US'],
            },
            shipping_options: [
                {
                    shipping_rate: 'shr_1TSuKWPR55nCEYvXsNoB48c5',
                },
            ],
        });

        res.json({ url: session.url });
    } catch (err) {
        console.error('Stripe Session Error:', err);
        res.status(500).json({ error: err.message });
    }
});

// API: Trigger Python Generator
app.post('/api/generate', (req, res) => {
    exec('python scripts/generate_shop.py', (error, stdout, stderr) => {
        if (error) {
            console.error(`exec error: ${error}`);
            return res.status(500).json({ error: error.message, output: stderr });
        }
        res.json({ success: true, output: stdout });
    });
});

// Error handling middleware for Multer and others
app.use((err, req, res, next) => {
    if (err instanceof multer.MulterError) {
        console.error('Global Multer Error:', err);
        return res.status(400).json({ 
            error: `Multer Error: ${err.message}`, 
            code: err.code,
            field: err.field 
        });
    }
    console.error('Server Error:', err);
    res.status(500).json({ error: 'Internal Server Error', details: err.message });
});

app.listen(PORT, () => {
    console.log(`Admin Server is running on http://localhost:${PORT}`);
    console.log(`Open Dashboard at: http://localhost:${PORT}/admin/index.html`);
});
