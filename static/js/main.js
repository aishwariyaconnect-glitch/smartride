// SmartRide Interactive Scripts

document.addEventListener('DOMContentLoaded', function () {

    // Auto-dismiss Flash Alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Date Range Cost Calculator & Validation
    const pickupInput = document.getElementById('pickup_date');
    const returnInput = document.getElementById('return_date');
    const vehicleIdInput = document.getElementById('vehicle_id');
    const pricePerDayInput = document.getElementById('price_per_day');

    const costBreakdownBox = document.getElementById('costBreakdownBox');
    const displayDays = document.getElementById('displayDays');
    const displayTotalCost = document.getElementById('displayTotalCost');
    const availabilityAlert = document.getElementById('availabilityAlert');
    const submitBookingBtn = document.getElementById('submitBookingBtn');

    if (pickupInput && returnInput) {
        // Set min date to today for pickup input
        const todayStr = new Date().toISOString().split('T')[0];
        pickupInput.setAttribute('min', todayStr);

        // When pickup date changes, update min return date
        pickupInput.addEventListener('change', function () {
            const pickupVal = pickupInput.value;
            if (pickupVal) {
                const nextDay = new Date(pickupVal);
                nextDay.setDate(nextDay.getDate() + 1);
                const nextDayStr = nextDay.toISOString().split('T')[0];
                returnInput.setAttribute('min', nextDayStr);

                if (returnInput.value && returnInput.value <= pickupVal) {
                    returnInput.value = nextDayStr;
                }
            }
            calculateCostAndCheckAvailability();
        });

        returnInput.addEventListener('change', calculateCostAndCheckAvailability);
    }

    function calculateCostAndCheckAvailability() {
        if (!pickupInput || !returnInput || !pickupInput.value || !returnInput.value) {
            if (costBreakdownBox) costBreakdownBox.classList.add('d-none');
            return;
        }

        const pickupDate = new Date(pickupInput.value);
        const returnDate = new Date(returnInput.value);

        if (returnDate <= pickupDate) {
            if (availabilityAlert) {
                availabilityAlert.className = 'alert alert-danger mt-3';
                availabilityAlert.innerHTML = '<i class="bi bi-exclamation-triangle-fill me-2"></i>Return date must be after pickup date.';
                availabilityAlert.classList.remove('d-none');
            }
            if (costBreakdownBox) costBreakdownBox.classList.add('d-none');
            if (submitBookingBtn) submitBookingBtn.disabled = true;
            return;
        }

        // Calculate days
        const diffTime = Math.abs(returnDate - pickupDate);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        const pricePerDay = parseFloat(pricePerDayInput ? pricePerDayInput.value : 0);
        const totalCost = diffDays * pricePerDay;

        // Display preliminary client-side calculation
        if (displayDays) displayDays.textContent = diffDays;
        if (displayTotalCost) displayTotalCost.textContent = '₹' + totalCost.toLocaleString('en-IN', { minimumFractionDigits: 2 });
        if (costBreakdownBox) costBreakdownBox.classList.remove('d-none');

        // Verify with server endpoint for double-booking conflict
        if (vehicleIdInput) {
            const formData = new FormData();
            formData.append('vehicle_id', vehicleIdInput.value);
            formData.append('pickup_date', pickupInput.value);
            formData.append('return_date', returnInput.value);

            fetch('/check-availability', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (availabilityAlert) {
                    availabilityAlert.classList.remove('d-none');
                    if (data.available) {
                        availabilityAlert.className = 'alert alert-success mt-3';
                        availabilityAlert.innerHTML = '<i class="bi bi-check-circle-fill me-2"></i>' + data.message;
                        if (submitBookingBtn) submitBookingBtn.disabled = false;
                    } else {
                        availabilityAlert.className = 'alert alert-danger mt-3';
                        availabilityAlert.innerHTML = '<i class="bi bi-x-circle-fill me-2"></i>' + data.message;
                        if (submitBookingBtn) submitBookingBtn.disabled = true;
                    }
                }
            })
            .catch(error => {
                console.error('Error checking availability:', error);
            });
        }
    }
});
