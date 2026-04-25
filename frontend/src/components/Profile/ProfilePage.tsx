import React from 'react';
import { BalanceCard } from '../BalanceCard';
import { Wallet } from '../Wallet';
import { Referral } from '../Referral';
import './ProfilePage.css';

const ProfilePage = () => {
  return (
    <div className="profile-page">
      <BalanceCard />

      {/* Мой питомец Section */}
      <section className="pet-section">
        <h2>Мой питомец</h2>
        <div className="pet-stats">
          <p>Уровень питомца: <span className="stat-value">1</span></p> {/* Placeholder value */}
          <p>Куплено питомцев: <span className="stat-value">5</span></p> {/* Placeholder value */}
          <p>Кормлений: <span className="stat-value">10</span></p> {/* Placeholder value */}
          <p>Поглаживаний: <span className="stat-value">20</span></p> {/* Placeholder value */}
        </div>
      </section>

      {/* Мой уютный дом Button Section */}
      <div className="cozy-home-button">
        <button onClick={() => alert('Navigating to Cozy Home')}>Мой уютный дом</button>
      </div>

      {/* Existing sections */}
      <Wallet />
      <Referral />
    </div>
  );
};

export default ProfilePage;