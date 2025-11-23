# Vibehuntr Branding Guide

## 🎨 Brand Colors

The Vibehuntr playground uses a modern, vibrant color scheme:

- **Primary**: `#FF6B6B` (Vibrant coral/red)
- **Background**: `#0F0F1E` (Deep dark blue)
- **Secondary**: `#1A1A2E` (Card backgrounds)
- **Text**: `#FFFFFF` (White)
- **Accent**: `#FF8E8E` (Light coral)

## 🔤 Typography

- **Font Family**: Lexend (Google Fonts)
- **Weights**: 300 (Light), 400 (Regular), 500 (Medium), 600 (Semi-bold), 700 (Bold)

## 🚀 Using the Branded Playground

### Option 1: ADK Playground with Custom Theme

The standard ADK playground now uses Vibehuntr branding:

```bash
make playground
```

The custom theme is automatically applied via `.streamlit/config.toml`

### Option 2: Custom Streamlit App

For full control, use the custom Vibehuntr playground:

```bash
streamlit run vibehuntr_playground.py
```

## 📁 Files Created

1. **`.streamlit/config.toml`** - Streamlit theme configuration
2. **`app/playground_style.py`** - Custom CSS and branding
3. **`app/vibehuntr_app.py`** - Branded app wrapper
4. **`vibehuntr_playground.py`** - Custom Streamlit interface

## 🎨 Design Elements

### Glassmorphism
Cards and containers use a glassmorphism effect with:
- Semi-transparent backgrounds
- Backdrop blur
- Subtle borders with brand color

### Gradients
- Primary buttons: Coral gradient
- Headers: Text gradient effect
- Background: Dark gradient

### Animations
- Button hover effects
- Smooth transitions
- Elevated shadows on interaction

## 🔧 Customization

### Changing Colors

Edit `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#YOUR_COLOR"
backgroundColor = "#YOUR_BG"
```

### Updating CSS

Edit `app/playground_style.py` to modify:
- Layout
- Typography
- Colors
- Animations
- Component styles

### Custom Logo

Replace the emoji in `VIBEHUNTR_HEADER` with:
- SVG logo
- Image file
- Custom HTML

## 📱 Responsive Design

The theme is optimized for:
- Desktop (1920x1080+)
- Laptop (1366x768+)
- Tablet (768x1024+)
- Mobile (375x667+)

## ✨ Features

### Dark Mode
- Native dark theme
- High contrast for readability
- Reduced eye strain

### Accessibility
- WCAG 2.1 AA compliant colors
- Clear focus states
- Readable font sizes

### Performance
- Minimal CSS overhead
- Optimized animations
- Fast load times

## 🎯 Brand Guidelines

### Do's
✅ Use the official color palette
✅ Maintain consistent spacing
✅ Use Lexend font family
✅ Keep animations subtle
✅ Ensure high contrast

### Don'ts
❌ Don't use off-brand colors
❌ Don't mix multiple font families
❌ Don't add heavy animations
❌ Don't reduce contrast
❌ Don't clutter the interface

## 🚀 Next Steps

1. **Test the playground:**
   ```bash
   make playground
   ```

2. **Customize further:**
   - Edit `.streamlit/config.toml`
   - Modify `app/playground_style.py`

3. **Deploy:**
   - The branding works in production
   - No additional setup needed

## 📸 Screenshots

The branded playground features:
- 🎉 Vibehuntr logo and tagline
- 🌈 Gradient text effects
- 💎 Glassmorphism cards
- 🎨 Coral accent colors
- 🌙 Dark theme background

## 🔗 Resources

- [Streamlit Theming Docs](https://docs.streamlit.io/library/advanced-features/theming)
- [Google Fonts - Lexend](https://fonts.google.com/specimen/Lexend)
- [Vibehuntr Website](https://vibehuntr.io)

Enjoy your beautifully branded Vibehuntr playground! 🎉
