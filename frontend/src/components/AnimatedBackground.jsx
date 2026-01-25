import React, { useEffect, useRef } from 'react';

/**
 * AnimatedBackground - Futuristic particle system background
 * 
 * Features:
 * - Floating gradient orbs
 * - Connecting lines between nearby particles
 * - Mouse interaction (particles avoid cursor)
 * - Performance optimized with requestAnimationFrame
 */
const AnimatedBackground = () => {
    const canvasRef = useRef(null);
    const particlesRef = useRef([]);
    const mouseRef = useRef({ x: null, y: null });
    const animationRef = useRef(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');

        // Set canvas size
        const resizeCanvas = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        // Particle configuration
        const particleCount = 80;
        const connectionDistance = 150;
        const colors = [
            'rgba(139, 92, 246, 0.6)',  // Violet
            'rgba(6, 182, 212, 0.6)',   // Cyan
            'rgba(236, 72, 153, 0.4)',  // Pink
            'rgba(34, 211, 238, 0.5)',  // Light Cyan
        ];

        // Initialize particles
        class Particle {
            constructor() {
                this.reset();
            }

            reset() {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.size = Math.random() * 3 + 1;
                this.speedX = (Math.random() - 0.5) * 0.5;
                this.speedY = (Math.random() - 0.5) * 0.5;
                this.color = colors[Math.floor(Math.random() * colors.length)];
                this.opacity = Math.random() * 0.5 + 0.3;
                this.pulseSpeed = Math.random() * 0.02 + 0.01;
                this.pulseOffset = Math.random() * Math.PI * 2;
            }

            update(time) {
                // Move particle
                this.x += this.speedX;
                this.y += this.speedY;

                // Pulse effect
                this.currentSize = this.size + Math.sin(time * this.pulseSpeed + this.pulseOffset) * 0.5;

                // Mouse repulsion
                if (mouseRef.current.x !== null) {
                    const dx = this.x - mouseRef.current.x;
                    const dy = this.y - mouseRef.current.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    if (distance < 100) {
                        const force = (100 - distance) / 100;
                        this.x += dx * force * 0.02;
                        this.y += dy * force * 0.02;
                    }
                }

                // Wrap around edges
                if (this.x < 0) this.x = canvas.width;
                if (this.x > canvas.width) this.x = 0;
                if (this.y < 0) this.y = canvas.height;
                if (this.y > canvas.height) this.y = 0;
            }

            draw(ctx) {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.currentSize, 0, Math.PI * 2);
                ctx.fillStyle = this.color;
                ctx.fill();

                // Glow effect
                ctx.shadowBlur = 15;
                ctx.shadowColor = this.color;
                ctx.fill();
                ctx.shadowBlur = 0;
            }
        }

        // Create particles
        particlesRef.current = Array.from({ length: particleCount }, () => new Particle());

        // Draw connections between nearby particles
        const drawConnections = (particles) => {
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const distance = Math.sqrt(dx * dx + dy * dy);

                    if (distance < connectionDistance) {
                        const opacity = (1 - distance / connectionDistance) * 0.3;
                        ctx.beginPath();
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.strokeStyle = `rgba(139, 92, 246, ${opacity})`;
                        ctx.lineWidth = 0.5;
                        ctx.stroke();
                    }
                }
            }
        };

        // Animation loop
        let time = 0;
        const animate = () => {
            time += 1;
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Draw gradient background overlay
            const gradient = ctx.createRadialGradient(
                canvas.width * 0.3, canvas.height * 0.3, 0,
                canvas.width * 0.3, canvas.height * 0.3, canvas.width * 0.8
            );
            gradient.addColorStop(0, 'rgba(139, 92, 246, 0.03)');
            gradient.addColorStop(1, 'transparent');
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Second gradient
            const gradient2 = ctx.createRadialGradient(
                canvas.width * 0.8, canvas.height * 0.7, 0,
                canvas.width * 0.8, canvas.height * 0.7, canvas.width * 0.6
            );
            gradient2.addColorStop(0, 'rgba(6, 182, 212, 0.03)');
            gradient2.addColorStop(1, 'transparent');
            ctx.fillStyle = gradient2;
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Update and draw particles
            particlesRef.current.forEach(particle => {
                particle.update(time);
                particle.draw(ctx);
            });

            // Draw connections
            drawConnections(particlesRef.current);

            animationRef.current = requestAnimationFrame(animate);
        };

        animate();

        // Mouse tracking
        const handleMouseMove = (e) => {
            mouseRef.current.x = e.clientX;
            mouseRef.current.y = e.clientY;
        };

        const handleMouseLeave = () => {
            mouseRef.current.x = null;
            mouseRef.current.y = null;
        };

        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('mouseleave', handleMouseLeave);

        // Cleanup
        return () => {
            window.removeEventListener('resize', resizeCanvas);
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseleave', handleMouseLeave);
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
        };
    }, []);

    return (
        <canvas
            ref={canvasRef}
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                zIndex: -1,
                pointerEvents: 'none',
            }}
        />
    );
};

export default AnimatedBackground;
