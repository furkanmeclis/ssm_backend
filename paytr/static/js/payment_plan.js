document.addEventListener('DOMContentLoaded', function () {
    const finalPriceInput = document.getElementById('id_final_price');
    const discountInput = document.getElementById('id_discount');
    const totalPriceField = document.querySelector('.field-total_price_display div');

    // Add style for total_price field
    totalPriceField.style.fontSize = '18px';
    totalPriceField.style.fontWeight = 'bold';

    function updatetotalPrice() {
        const finalPrice = parseFloat(finalPriceInput.value) || 0;
        const discount = parseFloat(discountInput.value) || 0;
        const totalPrice = finalPrice + discount;

        totalPriceField.innerHTML = `<strong>Üstü çizili olarak gösterilecek indirim öncesi fiyatı: </strong>${totalPrice.toFixed(2)}`;
    }

    // Add event listeners to update total price when inputs change
    finalPriceInput.addEventListener('input', updatetotalPrice);
    discountInput.addEventListener('input', updatetotalPrice);

    // Initial update (for the case when editing an existing PaymentPlan)
    updatetotalPrice();
});
