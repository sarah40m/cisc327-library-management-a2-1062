import pytest
from unittest.mock import Mock
from services.payment_service import PaymentGateway
import services.library_service as library_service

# test for successful payment
def test_process_payment_success():
    """Test a successful payment using mock gateway."""
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = (True, "txn_123", "Success")

    success, txn_id, message = mock_gateway.process_payment("123456", 10.0, "Late fees")

    mock_gateway.process_payment.assert_called_once_with("123456", 10.0, "Late fees")
    assert success is True
    assert txn_id == "txn_123"
    assert "success" in message.lower()


# test for declined payment
def test_process_payment_declined():
    """Test payment declined by gateway."""
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = (False, None, "Declined")

    success, txn_id, message = mock_gateway.process_payment("123456", 10.0, "Late fees")

    mock_gateway.process_payment.assert_called_once_with("123456", 10.0, "Late fees")
    assert success is False
    assert txn_id is None
    assert "declined" in message.lower()


# test for invalid patron id
def test_process_payment_invalid_patron_id():
    """Test payment mock not called when patron id is invalid."""
    mock_gateway = Mock(spec=PaymentGateway)

    # simulate invalid patron before gateway call
    patron_id = "12"  # not 6 digits
    if len(patron_id) != 6:
        success, txn_id, message = False, None, "Invalid patron ID"

    mock_gateway.process_payment.assert_not_called()
    assert success is False
    assert "invalid patron" in message.lower()


# test for zero amount
def test_process_payment_zero_amount():
    """Test gateway mock not called when amount is zero."""
    mock_gateway = Mock(spec=PaymentGateway)

    amount = 0
    if amount <= 0:
        success, txn_id, message = False, None, "Invalid amount"

    mock_gateway.process_payment.assert_not_called()
    assert success is False
    assert "invalid amount" in message.lower()


# test for successful refund
def test_refund_payment_success():
    """Test refund processed successfully."""
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.return_value = (True, "Refund success")

    success, message = mock_gateway.refund_payment("txn_001", 10.0)

    mock_gateway.refund_payment.assert_called_once_with("txn_001", 10.0)
    assert success is True
    assert "refund" in message.lower()


# test for invalid transaction id
def test_refund_payment_invalid_transaction():
    """Test refund mock not called for invalid transaction id."""
    mock_gateway = Mock(spec=PaymentGateway)

    txn_id = "abc"
    if not txn_id.startswith("txn_"):
        success, message = False, "Invalid transaction ID"

    mock_gateway.refund_payment.assert_not_called()
    assert success is False
    assert "invalid transaction" in message.lower()


# test for invalid refund amounts
@pytest.mark.parametrize("amount", [-1, 0, 20])
def test_refund_payment_invalid_amount(amount):
    """Test refund mock not called for invalid amounts."""
    mock_gateway = Mock(spec=PaymentGateway)

    if amount <= 0 or amount > 15:
        success, message = False, "Invalid refund amount"

    mock_gateway.refund_payment.assert_not_called()
    assert success is False
    assert "invalid refund amount" in message.lower()

# test for book not found
def test_pay_late_fees_book_not_found(mocker):
    """Test when book cannot be found in database."""
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"fee_amount": 5.00})
    mocker.patch("services.library_service.database.get_book_by_id", return_value=None)

    mock_gateway = Mock(spec=PaymentGateway)

    success, message, transaction_id = library_service.pay_late_fees("123456", 1, mock_gateway)

    mock_gateway.process_payment.assert_not_called()
    assert success is False
    assert "book not found" in message.lower()
    assert transaction_id is None


# test for payment processing error
def test_pay_late_fees_gateway_exception(mocker):
    """Test network or API error during payment."""
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"fee_amount": 5.00})
    mocker.patch("services.library_service.database.get_book_by_id", return_value={"title": "Test Book"})

    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.side_effect = Exception("Network timeout")

    success, message, transaction_id = library_service.pay_late_fees("123456", 1, mock_gateway)

    mock_gateway.process_payment.assert_called_once()
    assert success is False
    assert "network timeout" in message.lower()
    assert transaction_id is None


# test for missing fee_amount key
def test_pay_late_fees_missing_fee_key(mocker):
    """Test when calculate_late_fee_for_book returns dict missing 'fee_amount' key."""
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"wrong_key": 5})
    mocker.patch("services.library_service.database.get_book_by_id", return_value={"title": "Test Book"})

    mock_gateway = Mock(spec=PaymentGateway)

    success, message, transaction_id = library_service.pay_late_fees("123456", 1, mock_gateway)

    mock_gateway.process_payment.assert_not_called()
    assert success is False
    assert "unable to calculate" in message.lower()


# test for refund amount exceeds maximum
def test_refund_late_fee_amount_exceeds_limit():
    """Test refund fails when amount exceeds $15 limit."""
    mock_gateway = Mock(spec=PaymentGateway)

    success, message = library_service.refund_late_fee_payment("txn_111", 20.0, mock_gateway)

    mock_gateway.refund_payment.assert_not_called()
    assert success is False
    assert "exceeds" in message.lower()


# test for refund payment failure
def test_refund_late_fee_gateway_failure():
    """Test refund fails when gateway returns failure."""
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.return_value = (False, "Refund failed")

    success, message = library_service.refund_late_fee_payment("txn_111", 5.0, mock_gateway)

    mock_gateway.refund_payment.assert_called_once_with("txn_111", 5.0)
    assert success is False
    assert "refund failed" in message.lower()


# test for refund gateway exception
def test_refund_late_fee_gateway_exception():
    """Test refund fails when gateway raises an exception."""
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.side_effect = Exception("Gateway unavailable")

    success, message = library_service.refund_late_fee_payment("txn_111", 5.0, mock_gateway)

    mock_gateway.refund_payment.assert_called_once()
    assert success is False
    assert "gateway unavailable" in message.lower()


# test for invalid patron id format (non-digit)
def test_pay_late_fees_invalid_patron_non_digit(mocker):
    """Test when patron ID contains letters instead of digits."""
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"fee_amount": 5.00})
    mocker.patch("services.library_service.database.get_book_by_id", return_value={"title": "Sample"})

    mock_gateway = Mock(spec=PaymentGateway)
    success, message, txn_id = library_service.pay_late_fees("abc123", 1, mock_gateway)

    mock_gateway.process_payment.assert_not_called()
    assert success is False
    assert "invalid patron id" in message.lower()


# test for late fee exactly zero
def test_pay_late_fees_exact_zero_fee(mocker):
    """Test when fee_amount is exactly zero."""
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"fee_amount": 0.0})
    mocker.patch("services.library_service.database.get_book_by_id", return_value={"title": "Zero Book"})

    mock_gateway = Mock(spec=PaymentGateway)
    success, message, txn_id = library_service.pay_late_fees("123456", 1, mock_gateway)

    mock_gateway.process_payment.assert_not_called()
    assert success is False
    assert "no late fees" in message.lower()


# test for negative fee (edge condition)
def test_pay_late_fees_negative_fee(mocker):
    """Test when fee_amount is negative (invalid edge case)."""
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"fee_amount": -2.00})
    mocker.patch("services.library_service.database.get_book_by_id", return_value={"title": "Bad Fee Book"})

    mock_gateway = Mock(spec=PaymentGateway)
    success, message, txn_id = library_service.pay_late_fees("123456", 1, mock_gateway)

    mock_gateway.process_payment.assert_not_called()
    assert success is False
    assert "no late fees" in message.lower()


# test for refund success followed by double-call prevention
def test_refund_late_fee_double_call():
    """Test refund called once and not twice."""
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.return_value = (True, "Refund processed")

    success, message = library_service.refund_late_fee_payment("txn_222", 5.0, mock_gateway)
    mock_gateway.refund_payment.assert_called_once_with("txn_222", 5.0)
    assert success is True
    assert "refund processed" in message.lower()

    # Ensure no duplicate refund was triggered
    mock_gateway.refund_payment.assert_called_once()


# test for refund with exception and large amount
def test_refund_late_fee_exception_large_amount():
    """Test exception raised during refund of large amount."""
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.side_effect = Exception("System error")

    success, message = library_service.refund_late_fee_payment("txn_333", 10.0, mock_gateway)

    mock_gateway.refund_payment.assert_called_once()
    assert success is False
    assert "system error" in message.lower()


# test for PaymentGateway invalid amount
def test_gateway_process_payment_invalid_amount():
    """Test direct PaymentGateway method with invalid amount."""
    gateway = PaymentGateway()
    success, txn, msg = gateway.process_payment("123456", -1, "Invalid Payment")
    assert success is False
    assert "invalid amount" in msg.lower()


# test for PaymentGateway payment over limit
def test_gateway_process_payment_over_limit():
    """Test direct PaymentGateway with amount exceeding limit."""
    gateway = PaymentGateway()
    success, txn, msg = gateway.process_payment("123456", 1500.0, "Over Limit Payment")
    assert success is False
    assert "exceeds limit" in msg.lower()


# test for PaymentGateway invalid patron ID
def test_gateway_process_payment_invalid_id():
    """Test invalid patron ID length."""
    gateway = PaymentGateway()
    success, txn, msg = gateway.process_payment("123", 20.0, "Short ID")
    assert success is False
    assert "invalid patron id" in msg.lower()


# test for PaymentGateway successful refund flow
def test_gateway_refund_payment_success():
    """Test full successful refund process through real PaymentGateway logic."""
    gateway = PaymentGateway()
    success, message = gateway.refund_payment("txn_999", 5.0)
    assert success is True
    assert "refund of $5.00" in message.lower()


# test for PaymentGateway invalid transaction refund
def test_gateway_refund_payment_invalid_transaction():
    """Test refund fails with invalid transaction id."""
    gateway = PaymentGateway()
    success, message = gateway.refund_payment("bad_id", 5.0)
    assert success is False
    assert "invalid transaction id" in message.lower()


# test for PaymentGateway verify_payment_status success
def test_gateway_verify_payment_status_success():
    """Test verify_payment_status returns completed for valid transaction."""
    gateway = PaymentGateway()
    result = gateway.verify_payment_status("txn_777")
    assert result["status"] == "completed"
    assert "txn_777" in result["transaction_id"]


# test for PaymentGateway verify_payment_status not found
def test_gateway_verify_payment_status_not_found():
    """Test verify_payment_status returns not_found for invalid transaction."""
    gateway = PaymentGateway()
    result = gateway.verify_payment_status("invalid")
    assert result["status"] == "not_found"
    assert "transaction not found" in result["message"].lower()