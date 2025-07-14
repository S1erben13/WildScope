/**
 * Global variables for storing product data and charts
 */
let productsData = [];
let filteredProducts = [];
let priceHistogramChart = null;
let discountRatingChart = null;

/**
 * Displays alert notifications
 * @param {string} message - The message to display
 * @param {string} type - Alert type (success, warning, danger, etc.)
 */
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
    }, 5000);
}

/**
 * Fetches products from the API
 */
async function fetchProducts() {
    try {
        const response = await fetch('http://localhost:8000/api/products/', {
            mode: 'cors',
            headers: {'Content-Type': 'application/json'}
        });
        if (!response.ok) throw new Error('Failed to load data');

        const data = await response.json();
        productsData = data.products;
        filteredProducts = [...productsData];

        const maxPrice = Math.ceil(Math.max(...productsData.map(p => p.price), 100000) / 1000) * 1000;
        updatePriceSlider(0, maxPrice);

        renderTable(filteredProducts);
        updateCharts(filteredProducts);
        return true;
    } catch (error) {
        console.error('Error:', error);
        return false;
    }
}

/**
 * Updates price slider range
 */
function updatePriceSlider(min, max) {
    const priceSlider = document.getElementById('priceSlider');
    document.getElementById('minPriceValue').textContent = formatNumber(min);
    document.getElementById('maxPriceValue').textContent = formatNumber(max);

    priceSlider.noUiSlider.updateOptions({
        range: {
            'min': min,
            'max': max
        },
        start: [min, max]
    });
}

/**
 * Sends product request to the server
 */
async function sendProductsRequest() {
    const submitBtn = document.getElementById('submitBtn');
    const searchQuery = document.getElementById('searchQuery').value.trim();
    const productsQuantity = document.getElementById('productsQuantity').value;

    if (!searchQuery) {
        showAlert('Please enter search query', 'warning');
        return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';

    try {
        const response = await fetch('/api/products/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: searchQuery,
                quantity: Number(productsQuantity)
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Server error');
        }

        await fetchProducts();
        applyFilters();
        applySort();
        showAlert('Products loaded successfully!', 'success');
        document.getElementById('searchQuery').value = '';
        document.getElementById('productsQuantity').value = '0';
    } catch (error) {
        console.error('Error:', error);
        showAlert('Error: ' + error.message, 'danger');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Отправить';
    }
}

/**
 * Initializes the page
 */
document.addEventListener('DOMContentLoaded', function() {
    if (!document.getElementById('productsTableBody') || !document.getElementById('priceSlider')) {
        console.error('Required DOM elements not found');
        return;
    }

    const priceSlider = document.getElementById('priceSlider');
    noUiSlider.create(priceSlider, {
        start: [0, 50000],
        connect: true,
        range: {
            'min': 0,
            'max': 50000
        },
        step: 100
    });

    priceSlider.noUiSlider.on('update', function(values) {
        const min = Math.round(values[0]);
        const max = Math.round(values[1]);
        document.getElementById('minPriceValue').textContent = formatNumber(min);
        document.getElementById('maxPriceValue').textContent = formatNumber(max);
        applyFilters();
    });

    // Add event listener for sort changes to update immediately
    document.getElementById('sortBy').addEventListener('change', applySort);
    document.getElementById('ratingFilter').addEventListener('input', applyFilters);
    document.getElementById('feedbackFilter').addEventListener('input', applyFilters);
    document.getElementById('resetFilters').addEventListener('click', resetFilters);

    fetchProducts();
});

/**
 * Renders products table
 */
function renderTable(products) {
    productsTableBody.innerHTML = '';

    products.forEach(product => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${product.product_name}</td>
            <td>${formatNumber(product.price)} ₽</td>
            <td>${formatNumber(product.discount_price)} ₽</td>
            <td>${product.rating}</td>
            <td>${formatNumber(product.feedbacks)}</td>
        `;
        productsTableBody.appendChild(row);
    });
}

/**
 * Applies filters to products
 */
function applyFilters() {
    if (!checkDataLoaded()) return;

    const priceRange = priceSlider.noUiSlider.get();
    const minPrice = parseInt(priceRange[0]);
    const maxPrice = parseInt(priceRange[1]);
    const minRating = parseFloat(ratingFilter.value) || 0;
    const minFeedbacks = parseInt(feedbackFilter.value) || 0;

    filteredProducts = productsData.filter(product => {
        return product.price >= minPrice &&
            product.price <= maxPrice &&
            product.rating >= minRating &&
            product.feedbacks >= minFeedbacks;
    });

    renderTable(filteredProducts);
    updateCharts(filteredProducts);
}

/**
 * Resets all filters
 */
function resetFilters() {
    priceSlider.noUiSlider.set([0, 50000]);
    ratingFilter.value = '4.0';
    feedbackFilter.value = '0';
    applyFilters();
}

/**
 * Applies sorting to products
 */
function applySort() {
    if (!checkDataLoaded()) return;

    const sortValue = sortBy.value;

    filteredProducts.sort((a, b) => {
        switch (sortValue) {
            case 'name_asc': return a.product_name.localeCompare(b.product_name);
            case 'name_desc': return b.product_name.localeCompare(a.product_name);
            case 'price_asc': return a.price - b.price;
            case 'price_desc': return b.price - a.price;
            case 'discount_price_asc': return a.discount_price - b.discount_price;
            case 'discount_price_desc': return b.discount_price - a.discount_price;
            case 'rating_asc': return a.rating - b.rating;
            case 'rating_desc': return b.rating - a.rating;
            case 'feedbacks_asc': return a.feedbacks - b.feedbacks;
            case 'feedbacks_desc': return b.feedbacks - a.feedbacks;
            default: return 0;
        }
    });

    renderTable(filteredProducts);
}

/**
 * Updates all charts
 */
function updateCharts(products) {
    updatePriceHistogram(products);
    updateDiscountRatingChart(products);
}

/**
 * Updates price histogram chart
 */
function updatePriceHistogram(products) {
    const ctx = document.getElementById('priceHistogram').getContext('2d');
    const priceRanges = [
        {min: 0, max: 9999, label: '0-9,999'},
        {min: 10000, max: 19999, label: '10,000-19,999'},
        {min: 20000, max: 29999, label: '20,000-29,999'},
        {min: 30000, max: 39999, label: '30,000-39,999'},
        {min: 40000, max: 50000, label: '40,000-50,000'}
    ];

    const labels = priceRanges.map(range => range.label);
    const data = priceRanges.map(range => {
        return products.filter(p => p.price >= range.min && p.price <= range.max).length;
    });

    if (priceHistogramChart) priceHistogramChart.destroy();

    priceHistogramChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of products',
                data: data,
                backgroundColor: 'rgba(54, 162, 235, 0.7)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Number of products' } },
                x: { title: { display: true, text: 'Price range (₽)' } }
            }
        }
    });
}

/**
 * Updates discount vs rating chart
 */
function updateDiscountRatingChart(products) {
    const ctx = document.getElementById('discountRatingChart').getContext('2d');
    const ratingGroups = {};
    const minRating = 0;
    const maxRating = 5;
    const step = 0.5;

    for (let r = minRating; r <= maxRating; r += step) {
        const ratingKey = r.toFixed(1);
        ratingGroups[ratingKey] = { totalDiscount: 0, count: 0 };
    }

    products.forEach(product => {
        const roundedRating = Math.round(product.rating * 2) / 2;
        const ratingKey = roundedRating.toFixed(1);
        const discount = ((product.price - product.discount_price) / product.price) * 100;

        if (ratingGroups[ratingKey]) {
            ratingGroups[ratingKey].totalDiscount += discount;
            ratingGroups[ratingKey].count++;
        }
    });

    const labels = [];
    const data = [];
    const backgroundColors = [];

    for (let r = minRating; r <= maxRating; r += step) {
        const ratingKey = r.toFixed(1);
        labels.push(ratingKey);

        if (ratingGroups[ratingKey] && ratingGroups[ratingKey].count > 0) {
            data.push(ratingGroups[ratingKey].totalDiscount / ratingGroups[ratingKey].count);
            const hue = (r / maxRating) * 120;
            backgroundColors.push(`hsla(${hue}, 70%, 50%, 0.2)`);
        } else {
            data.push(null);
            backgroundColors.push('rgba(200, 200, 200, 0.1)');
        }
    }

    if (discountRatingChart) discountRatingChart.destroy();

    discountRatingChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Average discount (%)',
                data: data,
                backgroundColor: backgroundColors,
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 2,
                tension: 0.1,
                fill: true,
                pointBackgroundColor: 'rgba(75, 192, 192, 1)',
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Discount: ${context.parsed.y.toFixed(2)}%`;
                        }
                    }
                }
            },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Average discount (%)' }, min: 0, max: 100 },
                x: { title: { display: true, text: 'Rating (step 0.5)' } }
            }
        }
    });
}

/**
 * Checks if data is loaded
 */
function checkDataLoaded() {
    if (!productsData || productsData.length === 0) {
        showAlert('Data not loaded yet. Please wait...', 'warning');
        return false;
    }
    return true;
}

/**
 * Formats numbers with thousands separators
 */
function formatNumber(num) {
    return new Intl.NumberFormat('ru-RU').format(num);
}