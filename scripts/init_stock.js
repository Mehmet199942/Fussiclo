const fs = require('fs');
const path = 'c:/Users/mehme/Desktop/cozastore-master/data/database.json';

const products = JSON.parse(fs.readFileSync(path, 'utf8'));

const updatedProducts = products.map(p => {
    if (!p.stock) {
        p.stock = {
            "S": 10,
            "M": 10,
            "L": 10,
            "XL": 10,
            "XXL": 10
        };
    }
    return p;
});

fs.writeFileSync(path, JSON.stringify(updatedProducts, null, 4));
console.log(`Updated ${updatedProducts.length} products with default stock.`);
