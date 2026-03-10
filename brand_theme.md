# Project Store - Brand Theme & Design Guidelines

This document outlines the core branding elements, aesthetics, and design choices used across the Project Store web application. It serves as a reference for the marketing and development teams.

## 1. Brand Logo

The official brand logo must be used consistently across all marketing materials and site headers.

![Project Store Logo](C:\Users\hamza.gemini\antigravity\brain\b903c727-c36a-48fa-a31f-b868dd626e4a\project_store_logo.png)

## 2. Typography

The primary font family used throughout the application provides a clean, modern, and readable experience.

- **Primary Font:** **Poppins**, sans-serif
- **Fallback Font:** sans-serif

**Usage Notes:**

- Standard text weight is regular.
- Headings and emphasized links use bold weight.
- Font sizing varies dynamically for responsiveness.

## 3. Color Palette

The color scheme is designed to balance a professional tech-focused look with clear, engaging calls to action.

### Primary Colors

- **Primary Dark Blue:** `#0f172a` (Used for specific dark theme elements and deep backgrounds)
- **Vibrant Blue:** `#007bff` (Used for primary headings, titles, and actionable icons like "Back to Top")
- **Registration Blue / Indigo:** `#3939cd` (Used heavily in the registration flow, progress bars, and step indicators)
- **Teal:** `teal` (Used for default submit buttons and success-state form borders)

### Neutral & Background Colors

- **Dark Grey:** `darkgrey` (Main body background reference)
- **Light Grey / Off-White Backgrounds:** `#f4f4f4`, `#e9ecef` (Used for carousels and inactive progress lines)
- **White:** `#ffffff` (Card backgrounds, inner containers)
- **Text Greys:** `#333333`, `#555555`, `gray` (Used for standard text, feature descriptions, and subtitles)
- **Glassmorphism Base:**
  - Background: `rgba(255, 255, 255, 0.65)`
  - Border: `rgba(255, 255, 255, 0.4)`

### Action & Alert Colors

- **Success / Add to Cart:** `#28a745` (Hover: `#218838`)
- **Danger / Price Highlights:** `#dc3545` (Used for displaying card prices and error states)
- **Slider Accent:** `rgb(35, 110, 43)` (Dark green)

## 4. Glassmorphic UI Components & Responsiveness

The entire application is built with a **mobile-first, responsive design** that fluidly adapts to any screen size (scaling from 1700px on large desktop screens down to 400px for mobile cards). A strong emphasis is placed on an interactive, dynamic user experience with modern **glassmorphic aesthetics**.

### Cards and Containers

- **Borders:** Soft borders (`2px solid #ddd`) with `8px` to `20px` border-radius for a smooth, rounded look.
- **Shadows:** A standard drop shadow (`0 2px 5px rgba(0,0,0,0.1)`) is applied to cards to lift them from the background. Larger shadows (`0 20px 25px -5px rgba(0,0,0,0.1)`) are used for more prominent components.
- **Glassmorphism:** Certain elevated elements leverage semi-transparent backgrounds (`rgba(255, 255, 255, 0.65)`) with soft, translucent white borders (`rgba(255, 255, 255, 0.4)`), creating a vibrant frosted-glass effect over the underlying thematic sections.

### Interactive Elements

- **Forms:** Inputs feature dynamic border colors. Success states change to teal, while error states change to red (`#ff0000`).
- **Animations:** The site features subtle micro-animations like infinite scrolling text carousels (`40s linear infinite`) and smooth transitions (`0.3s ease`) on sliding sidebars like the cart drawer.
- **Carousels/Sliders:** Swiper components are used extensively, featuring prominent navigation arrows and semi-transparent thumbnail navigation.

### Registration Flow

The multi-step registration process features a prominent, customized progress bar with circular icons (`80px x 80px`, white and `#3939cd`). The connecting lines dynamically fill in `#3939cd` as the user progresses.

## 5. Spacing and Alignment

- Elements are built mobile-first and responsive. Max-widths expand up to `1700px` on large screens but adapt smoothly down to `400px` for mobile cards.
- Ample padding is used inside cards and containers (e.g., `40px 0` for standard container padding) to let content breathe.
