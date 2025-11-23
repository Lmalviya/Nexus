import React from 'react';

const Footer = () => {
    return (
        <footer className="bg-gray-900 border-t border-gray-800 py-6 text-center text-gray-500 text-sm">
            <p>&copy; {new Date().getFullYear()} Nexus AI. All rights reserved.</p>
        </footer>
    );
};

export default Footer;
