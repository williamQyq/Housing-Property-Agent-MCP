import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

interface AnimatedListProps {
  children: React.ReactNode;
  className?: string;
  itemClassName?: string;
  staggerDelay?: number;
}

export const AnimatedList = ({ 
  children, 
  className, 
  itemClassName,
  staggerDelay = 100 
}: AnimatedListProps) => {
  const [visibleItems, setVisibleItems] = useState<Set<number>>(new Set());
  const observerRef = useRef<IntersectionObserver | null>(null);
  const itemRefs = useRef<(HTMLDivElement | null)[]>([]);

  // Create the observer once
  useEffect(() => {
    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const index = parseInt(entry.target.getAttribute('data-index') || '0');
          if (entry.isIntersecting) {
            setTimeout(() => {
              setVisibleItems(prev => new Set([...prev, index]));
            }, index * staggerDelay);
          }
        });
      },
      {
        threshold: 0.1,
        rootMargin: '20px'
      }
    );

    return () => {
      observerRef.current?.disconnect();
    };
  }, [staggerDelay]);

  const childArray = Array.isArray(children) ? children : [children];

  // Observe items whenever the number of children changes
  useEffect(() => {
    const obs = observerRef.current;
    if (!obs) return;
    // Unobserve any previous refs to avoid duplicates
    itemRefs.current.forEach((ref) => {
      if (ref) obs.unobserve(ref);
    });
    // Observe current refs
    itemRefs.current.forEach((ref) => {
      if (ref) obs.observe(ref);
    });
  }, [childArray.length]);

  return (
    <div className={className}>
      {childArray.map((child, index) => (
        <div
          key={index}
          ref={(el) => (itemRefs.current[index] = el)}
          data-index={index}
          className={cn(
            "opacity-0 translate-y-4 transition-all duration-500 ease-out",
            visibleItems.has(index) && "opacity-100 translate-y-0",
            itemClassName
          )}
        >
          {child}
        </div>
      ))}
    </div>
  );
};
