import React, { useState } from "react";
import ConfirmationModal from "../components/auth/ConfirmationModal";

interface ContactUsButtonProps {
  buttonClass?: string;
  buttonText?: string;
}

const ContactUsButton: React.FC<ContactUsButtonProps> = ({
  buttonClass = "auth-cta", // default to same styling as login/register
  buttonText = "Contact us",
}) => {
  const [modalOpen, setModalOpen] = useState(false);

  const handleContactConfirm = () => {
    setModalOpen(false);
    window.location.href = `mailto:noreply.ntuvote@gmail.com?subject=${encodeURIComponent(
      "Enquiry about CryptoVote Application"
    )}`;
  };

  return (
    <>
      <button onClick={() => setModalOpen(true)} className={buttonClass}>
        {buttonText}
      </button>

      <ConfirmationModal
        isOpen={modalOpen}
        title="Contact Administrator"
        message="You will be directed to your mailing application to send the admin developer your inquiries."
        onConfirm={handleContactConfirm}
        onCancel={() => setModalOpen(false)}
      />
    </>
  );
};

export default ContactUsButton;
