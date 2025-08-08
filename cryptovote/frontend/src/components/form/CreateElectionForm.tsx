// components/CreateElectionForm.tsx
import React, { useState, useEffect } from 'react';

const CreateElectionForm: React.FC<{ email: string }> = ({ email }) => {
  const [electionId, setElectionId] = useState('');
  const [electionName, setElectionName] = useState('');
  const [ip, setIp] = useState('');

  useEffect(() => {
    fetch('https://api64.ipify.org?format=json')
      .then((res) => res.json())
      .then((data) => setIp(data.ip))
      .catch(() => setIp(''));
  }, []);

  const handleCreate = async () => {
    if (!electionId || !electionName) {
      alert('Please fill in both ID and name.');
      return;
    }

    const res = await fetch('/admin/election/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: electionId,
        name: electionName,
        admin_email: email,
        ip_addr: ip,
      }),
    });

    const data = await res.json();
    if (res.ok) {
      alert(data.message);
      setElectionId('');
      setElectionName('');
    } else {
      alert(data.error || 'Failed to create election.');
    }
  };

  return (
    <div className="create-election-box">
      <input
        type="text"
        placeholder="Election ID (unique)"
        value={electionId}
        onChange={(e) => setElectionId(e.target.value)}
      />
      <input
        type="text"
        placeholder="Election Name"
        value={electionName}
        onChange={(e) => setElectionName(e.target.value)}
      />
      <button onClick={handleCreate}>+ Create New</button>
    </div>
  );
};

export default CreateElectionForm;
