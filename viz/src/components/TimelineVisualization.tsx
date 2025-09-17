'use client';

import React, { useMemo, useRef, useCallback, useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Chip,
  Box,
  Tooltip,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import ministersData from '../data/ministers_combined.json';

const TimelineContainer = styled(Box)(({ theme }) => ({
  position: 'relative',
  width: '100%',
  height: '85vh',
  overflow: 'auto',
  border: `1px solid ${theme.palette.divider}`,
  borderRadius: theme.shape.borderRadius,
}));

const TimelineContent = styled(Box)({
  position: 'relative',
  display: 'flex',
  flexDirection: 'column',
});

const MinistryRow = styled(Box)(() => ({
  display: 'flex',
  alignItems: 'center',
  height: '20px',
  position: 'relative',
}));

const MinistryLabel = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'isHovered',
})<{ isHovered?: boolean }>(({ theme, isHovered }) => ({
  width: '300px',
  minWidth: '300px',
  maxWidth: '300px',
  padding: theme.spacing(0.5),
  backgroundColor: isHovered ? theme.palette.action.hover : theme.palette.background.paper,
  borderRight: `1px solid ${theme.palette.divider}`,
  position: 'sticky',
  left: 0,
  zIndex: 2,
  display: 'flex',
  alignItems: 'center',
  fontSize: '0.875rem',
  fontWeight: isHovered ? 600 : 500,
  boxSizing: 'border-box',
  overflow: 'hidden',
  height: '20px',
  transition: theme.transitions.create(['background-color', 'font-weight']),
  [theme.breakpoints.down('md')]: {
    width: '150px',
    minWidth: '150px',
    maxWidth: '150px',
    padding: theme.spacing(0.25),
    fontSize: '0.75rem',
    height: '20px',
  },
}));

const MinistryTimeline = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'timelineWidth',
})<{ timelineWidth: number }>(({ timelineWidth, theme }) => ({
  flex: 1,
  position: 'relative',
  height: '20px',
  width: `${timelineWidth}px`,
  minWidth: `${timelineWidth}px`, // Dynamic width based on zoom
  backgroundColor: theme.palette.background.paper,
}));

const MinisterBar = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'isPersonHighlighted',
})<{ isPersonHighlighted?: boolean }>(({ theme, isPersonHighlighted }) => ({
  position: 'absolute',
  height: '20px',
  margin: '0',
  border: isPersonHighlighted
    ? `2px solid ${theme.palette.primary.main}`
    : `1px solid ${theme.palette.divider}`,
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  fontSize: '0.75rem',
  fontWeight: isPersonHighlighted ? 600 : 500,
  overflow: 'hidden',
  whiteSpace: 'nowrap',
  boxShadow: isPersonHighlighted ? theme.shadows[3] : 'none',
  zIndex: isPersonHighlighted ? 11 : 'auto',
  '&:hover': {
    transform: 'translateY(-1px)',
    boxShadow: theme.shadows[2],
    zIndex: 10,
  },
  transition: theme.transitions.create(['transform', 'box-shadow', 'border', 'font-weight']),
}));

const GovernmentRow = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  height: '20px',
  position: 'sticky',
  top: '30px', // Account for year timeline row height
  backgroundColor: theme.palette.background.paper,
  zIndex: 3,
  width: '100%',
  '& > *': {
    backgroundColor: 'inherit',
  },
}));

const PrimeMinisterRow = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  height: '20px',
  position: 'sticky',
  top: '50px', // Account for year timeline + government row height (30px + 20px)
  backgroundColor: theme.palette.background.paper,
  zIndex: 3,
  width: '100%',
  '& > *': {
    backgroundColor: 'inherit',
  },
}));

const GovernmentBar = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'isSelected',
})<{ isSelected?: boolean }>(({ theme, isSelected }) => ({
  position: 'absolute',
  height: '20px',
  margin: '0',
  border: isSelected
    ? `2px solid ${theme.palette.primary.main}`
    : `1px solid ${theme.palette.divider}`,
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  fontSize: '0.75rem',
  fontWeight: 600,
  overflow: 'hidden',
  whiteSpace: 'nowrap',
  borderRadius: '2px',
  boxShadow: isSelected ? theme.shadows[2] : 'none',
  '&:hover': {
    transform: 'translateY(-1px)',
    boxShadow: theme.shadows[3],
    zIndex: 10,
  },
  transition: theme.transitions.create(['transform', 'box-shadow', 'border']),
}));

const DateHoverIndicator = styled(Box)(({ theme }) => ({
  position: 'fixed',
  backgroundColor: theme.palette.primary.main,
  color: theme.palette.primary.contrastText,
  padding: theme.spacing(0.5, 1),
  borderRadius: theme.shape.borderRadius,
  fontSize: '0.75rem',
  fontWeight: 500,
  zIndex: 1000,
  pointerEvents: 'none',
  boxShadow: theme.shadows[2],
  transform: 'translateX(-50%)',
}));

const YearTimelineRow = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  height: '30px',
  backgroundColor: theme.palette.grey[50],
  position: 'sticky',
  top: 0,
  zIndex: 2,
  width: '100%',
  '& > *': {
    backgroundColor: 'inherit',
  },
}));

const YearTimeline = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'timelineWidth',
})<{ timelineWidth: number }>(({ timelineWidth, theme }) => ({
  flex: 1,
  position: 'relative',
  height: '30px',
  width: `${timelineWidth}px`,
  minWidth: `${timelineWidth}px`,
  backgroundColor: theme.palette.grey[50],
}));


const YearIndicator = styled(Box)(({ theme }) => ({
  position: 'absolute',
  height: '100%',
  display: 'flex',
  alignItems: 'center',
  fontSize: '0.7rem',
  fontWeight: 600,
  color: theme.palette.text.primary,
  backgroundColor: theme.palette.background.paper,
  padding: theme.spacing(0, 0.5),
  borderRadius: '2px',
  '&::after': {
    content: '""',
    position: 'absolute',
    width: '1px',
    height: '100vh',
    backgroundColor: theme.palette.divider,
    opacity: 0.3,
    left: '50%',
    top: 0,
    transform: 'translateX(-50%)',
  },
}));

interface Minister {
  name: string;
  ministry: {
    en: string;
    sl: string;
  };
  ministry_code: string;
  start_date: string;
  end_date: string;
  title: {
    en: string;
    sl: string;
  };
}

interface Government {
  number: number;
  name: {
    en: string;
    sl: string;
  };
  period: {
    start_date: string;
    end_date: string;
    duration_days: number;
  };
  leadership: {
    prime_minister: {
      name: string;
    };
  };
  ministers: Minister[];
  political_composition?: {
    coalition: {
      en: string;
      sl: string;
    };
    parties: string[];
    ideology: {
      en: string;
      sl: string;
    };
  };
}

// Color scheme based on how many government roles a person has held
const ROLE_FREQUENCY_COLORS = {
  1: '#e8f5e8',     // Light green for 1 role
  2: '#c8e6c9',     // Medium-light green for 2 roles
  3: '#a5d6a7',     // Medium green for 3 roles
  4: '#81c784',     // Medium-dark green for 4 roles
  5: '#66bb6a',     // Dark green for 5 roles
  6: '#4caf50',     // Darker green for 6 roles
  7: '#43a047',     // Very dark green for 7+ roles
  8: '#388e3c',     // Darkest green for 8+ roles
  default: '#2e7d32' // Fallback for 9+ roles
};

// Function to count how many government roles each person has held (including prime minister positions)
const countPersonRoles = (governments: Government[]) => {
  const personRoleCount = new Map<string, number>();

  governments.forEach(government => {
    // Count prime minister role
    const pmName = government.leadership.prime_minister.name;
    const currentPMCount = personRoleCount.get(pmName) || 0;
    personRoleCount.set(pmName, currentPMCount + 1);

    // Count minister roles
    government.ministers.forEach(minister => {
      const currentCount = personRoleCount.get(minister.name) || 0;
      personRoleCount.set(minister.name, currentCount + 1);
    });
  });

  return personRoleCount;
};

// Function to get color based on role frequency
const getPersonColor = (personName: string, roleCount: Map<string, number>) => {
  const count = roleCount.get(personName) || 1;

  if (count >= 9) return ROLE_FREQUENCY_COLORS.default;
  if (count >= 8) return ROLE_FREQUENCY_COLORS[8];
  if (count >= 7) return ROLE_FREQUENCY_COLORS[7];
  if (count >= 6) return ROLE_FREQUENCY_COLORS[6];
  if (count >= 5) return ROLE_FREQUENCY_COLORS[5];
  if (count >= 4) return ROLE_FREQUENCY_COLORS[4];
  if (count >= 3) return ROLE_FREQUENCY_COLORS[3];
  if (count >= 2) return ROLE_FREQUENCY_COLORS[2];
  return ROLE_FREQUENCY_COLORS[1];
};

const calculateFitToScreenZoom = () => {
  // Get the timeline span in days
  const governments = ministersData.governments as Government[];
  const allDates = governments.flatMap(gov => [
    new Date(gov.period.start_date),
    new Date(gov.period.end_date)
  ]);
  const start = new Date(Math.min(...allDates.map(d => d.getTime())));
  const end = new Date(Math.max(...allDates.map(d => d.getTime())));
  const totalDays = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));

  // Get available screen width (accounting for ministry labels)
  const screenWidth = typeof window !== 'undefined' ? window.innerWidth : 1200;
  const isMobile = screenWidth < 768;
  const ministryLabelWidth = isMobile ? 150 : 300;
  const availableWidth = screenWidth - ministryLabelWidth - 100; // Extra margin for safety

  // Calculate zoom level needed to fit timeline to screen
  const basePxPerDay = 2;
  const requiredPxPerDay = Math.max(0.1, availableWidth / totalDays);
  const fitZoom = requiredPxPerDay / basePxPerDay;

  // Clamp between reasonable bounds
  return Math.max(0.05, Math.min(2, fitZoom));
};

export default function TimelineVisualization() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [zoomLevel, setZoomLevel] = useState(0.05); // Start with default, will be updated after hydration
  const [mouseDate, setMouseDate] = useState<string | null>(null);
  const [mousePosition, setMousePosition] = useState<{ x: number; y: number } | null>(null);
  const [selectedGovernment, setSelectedGovernment] = useState<number | null>(null);
  const [clickedBarDate, setClickedBarDate] = useState<{ date: string; position: { x: number; y: number } } | null>(null);
  const [zoomInput, setZoomInput] = useState('5.0'); // Start with default, will be updated after hydration
  const [isHydrated, setIsHydrated] = useState(false);
  const [language, setLanguage] = useState<'en' | 'sl'>('en');
  const [sortMode, setSortMode] = useState<'first-appearance' | 'frequency'>('first-appearance');
  const [hoveredMinistry, setHoveredMinistry] = useState<string | null>(null);
  const [hoveredPerson, setHoveredPerson] = useState<string | null>(null);

  // Initialize zoom after hydration to prevent SSR mismatch
  useEffect(() => {
    setIsHydrated(true);
    const fitZoom = calculateFitToScreenZoom();
    setZoomLevel(fitZoom);
    setZoomInput((fitZoom * 100).toFixed(1));
  }, []);

  // Update zoom when window is resized
  useEffect(() => {
    if (!isHydrated) return;

    const handleResize = () => {
      const newFitZoom = calculateFitToScreenZoom();
      setZoomLevel(newFitZoom);
      setZoomInput((newFitZoom * 100).toFixed(1));
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isHydrated]);

  const { baseData, governmentData, timelineStart, timelineEnd, pixelsPerDay, totalTimelineWidth } = useMemo(() => {
    const governments = ministersData.governments as Government[];

    // Count how many roles each person has held across all governments
    const personRoleCount = countPersonRoles(governments);

    // Find overall timeline bounds
    const allDates = governments.flatMap(gov => [
      new Date(gov.period.start_date),
      new Date(gov.period.end_date)
    ]);
    const start = new Date(Math.min(...allDates.map(d => d.getTime())));
    const end = new Date(Math.max(...allDates.map(d => d.getTime())));

    // Calculate pixels per day for timeline width (adjustable with zoom)
    const basePxPerDay = 2;
    const pxPerDay = basePxPerDay * zoomLevel;

    // Calculate total timeline width
    const totalDays = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
    const totalWidth = Math.max(totalDays * pxPerDay, 800); // Minimum 800px

    // Get all unique ministries with their first appearance dates and frequencies
    const ministriesWithFirstDate = new Map<string, Date>();
    const ministriesWithFrequency = new Map<string, number>();

    governments.forEach(gov => {
      gov.ministers.forEach(minister => {
        const ministryName = language === 'en' ? minister.ministry.en : minister.ministry.sl;
        const startDate = new Date(minister.start_date);

        // Track first appearance
        if (!ministriesWithFirstDate.has(ministryName) ||
            startDate < ministriesWithFirstDate.get(ministryName)!) {
          ministriesWithFirstDate.set(ministryName, startDate);
        }

        // Track frequency (count each minister appointment)
        const currentCount = ministriesWithFrequency.get(ministryName) || 0;
        ministriesWithFrequency.set(ministryName, currentCount + 1);
      });
    });

    // Sort ministries based on selected mode
    let ministriesArray: string[];
    if (sortMode === 'frequency') {
      ministriesArray = Array.from(ministriesWithFrequency.entries())
        .sort(([, freqA], [, freqB]) => freqB - freqA) // Descending frequency
        .map(([ministry]) => ministry);
    } else {
      // Default: sort by first appearance date
      ministriesArray = Array.from(ministriesWithFirstDate.entries())
        .sort(([, dateA], [, dateB]) => dateA.getTime() - dateB.getTime())
        .map(([ministry]) => ministry);
    }

    // Process government data (still use government colors for government bar)
    const GOVERNMENT_COLORS = [
      '#e3f2fd', '#f3e5f5', '#e8f5e8', '#fff3e0', '#fce4ec',
      '#f1f8e9', '#e0f2f1', '#e8eaf6', '#fff8e1', '#fde7f3',
      '#e0f7fa', '#f9fbe7', '#efebe9', '#f3e5f5'
    ];

    const processedGovernments = governments.map((gov, govIndex) => ({
      number: gov.number,
      name: language === 'en' ? gov.name.en : gov.name.sl,
      startDate: gov.period.start_date,
      endDate: gov.period.end_date,
      primeMinister: gov.leadership.prime_minister.name,
      primeMinisterColor: getPersonColor(gov.leadership.prime_minister.name, personRoleCount), // Add PM color
      primeMinisterRoleCount: personRoleCount.get(gov.leadership.prime_minister.name) || 1, // Add PM role count
      color: GOVERNMENT_COLORS[govIndex % GOVERNMENT_COLORS.length]
    }));

    // Process ministers by ministry
    const processedMinistries = ministriesArray.map(ministry => {
      const ministers = governments.flatMap((gov, govIndex) => {
        return gov.ministers
          .filter(minister => (language === 'en' ? minister.ministry.en : minister.ministry.sl) === ministry)
          .map(minister => ({
            ...minister,
            governmentNumber: gov.number,
            governmentName: language === 'en' ? gov.name.en : gov.name.sl,
            governmentColor: GOVERNMENT_COLORS[govIndex % GOVERNMENT_COLORS.length],
            personColor: getPersonColor(minister.name, personRoleCount), // New person-based color
            roleCount: personRoleCount.get(minister.name) || 1, // Add role count for tooltip
            primeMinister: gov.leadership.prime_minister.name
          }));
      });

      return {
        name: ministry,
        ministers
      };
    });

    return {
      baseData: processedMinistries,
      governmentData: processedGovernments,
      timelineStart: start,
      timelineEnd: end,
      pixelsPerDay: pxPerDay,
      totalTimelineWidth: totalWidth
    };
  }, [zoomLevel, language, sortMode]);

  // Reorder ministries based on selected government
  const processedData = useMemo(() => {
    if (!selectedGovernment) {
      return baseData;
    }

    // Find ministries that have ministers in the selected government
    const ministriesWithSelectedGov = new Set<string>();
    const ministriesWithoutSelectedGov: typeof baseData = [];

    baseData.forEach(ministry => {
      const hasSelectedGovMinisters = ministry.ministers.some(
        minister => minister.governmentNumber === selectedGovernment
      );

      if (hasSelectedGovMinisters) {
        ministriesWithSelectedGov.add(ministry.name);
      } else {
        ministriesWithoutSelectedGov.push(ministry);
      }
    });

    // Get ministries with selected government ministers, maintaining their original order
    const ministriesWithSelectedGovData = baseData.filter(ministry =>
      ministriesWithSelectedGov.has(ministry.name)
    );

    // Return reordered array: selected government ministries first, then others
    return [...ministriesWithSelectedGovData, ...ministriesWithoutSelectedGov];
  }, [baseData, selectedGovernment]);

  const isMobileDevice = useCallback(() => {
    return window.innerWidth < 768 || 'ontouchstart' in window;
  }, []);

  const handleGovernmentClick = useCallback((governmentNumber: number) => {
    setSelectedGovernment(prev => prev === governmentNumber ? null : governmentNumber);
  }, []);

  const handleBarClick = useCallback((event: React.MouseEvent, startDate: string, endDate: string) => {
    if (!isMobileDevice()) return;

    event.stopPropagation();

    const container = scrollRef.current;
    if (!container) return;

    const rect = container.getBoundingClientRect();

    // Calculate the middle date of the clicked bar
    const startTime = new Date(startDate).getTime();
    const endTime = new Date(endDate).getTime();
    const middleTime = startTime + (endTime - startTime) / 2;
    const middleDate = new Date(middleTime);

    const formattedDate = middleDate.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });

    setClickedBarDate({
      date: formattedDate,
      position: { x: event.clientX, y: rect.top + 5 } // Fixed position like hover tooltip
    });

    // Clear the indicator after 3 seconds
    setTimeout(() => {
      setClickedBarDate(null);
    }, 3000);
  }, [isMobileDevice]);

  const getPositionFromDate = useCallback((date: string) => {
    const targetDate = new Date(date);
    const daysDiff = Math.ceil((targetDate.getTime() - timelineStart.getTime()) / (1000 * 60 * 60 * 24));
    return daysDiff * pixelsPerDay;
  }, [timelineStart, pixelsPerDay]);

  const getWidthFromDates = useCallback((startDate: string, endDate: string) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const daysDiff = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
    return daysDiff * pixelsPerDay; // No minimum width constraint
  }, [pixelsPerDay]);

  const getDateFromPosition = useCallback((pixelPosition: number) => {
    const daysFromStart = pixelPosition / pixelsPerDay;
    const targetDate = new Date(timelineStart.getTime() + daysFromStart * 24 * 60 * 60 * 1000);
    return targetDate.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }, [pixelsPerDay, timelineStart]);

  const handleMouseMove = useCallback((event: React.MouseEvent) => {
    const container = scrollRef.current;
    if (!container) return;

    const rect = container.getBoundingClientRect();
    const scrollLeft = container.scrollLeft;

    // Account for ministry label width - responsive to screen size
    const isMobile = window.innerWidth < 768; // md breakpoint
    const labelWidth = isMobile ? 150 : 300;
    const mouseX = event.clientX - rect.left + scrollLeft - labelWidth;

    if (mouseX >= 0) {
      const date = getDateFromPosition(mouseX);
      setMouseDate(date);
      // Fixed position: x relative to viewport, y aligned with year timeline from container top
      setMousePosition({
        x: event.clientX,
        y: rect.top + 5 // 5px from container top aligns better with year row
      });
    } else {
      setMouseDate(null);
      setMousePosition(null);
    }
  }, [getDateFromPosition]);

  const handleMouseLeave = useCallback(() => {
    setMouseDate(null);
    setMousePosition(null);
    setHoveredMinistry(null);
    setHoveredPerson(null);
  }, []);

  // Generate year markers
  const yearMarkers = useMemo(() => {
    const markers = [];
    const startYear = timelineStart.getFullYear();
    const endYear = timelineEnd.getFullYear();

    for (let year = startYear; year <= endYear; year += 2) { // Every 2 years
      const yearDate = new Date(year, 0, 1);
      const position = getPositionFromDate(yearDate.toISOString().split('T')[0]);
      markers.push({ year, position });
    }
    return markers;
  }, [timelineStart, timelineEnd, getPositionFromDate]);

  const handleZoom = (delta: number) => {
    const newZoom = Math.max(0.05, Math.min(5, zoomLevel + delta));
    setZoomLevel(newZoom);
    setZoomInput((newZoom * 100).toFixed(1));
  };

  const handleZoomInputChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setZoomInput(event.target.value);
  }, []);

  const handleZoomInputSubmit = useCallback(() => {
    const numericValue = parseFloat(zoomInput);
    if (!isNaN(numericValue) && numericValue > 0) {
      const clampedZoom = Math.max(0.05, Math.min(500, numericValue / 100));
      setZoomLevel(clampedZoom);
      setZoomInput((clampedZoom * 100).toFixed(1));
    } else {
      // Reset to current zoom if invalid
      setZoomInput((zoomLevel * 100).toFixed(1));
    }
  }, [zoomInput, zoomLevel]);

  const handleZoomInputKeyPress = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleZoomInputSubmit();
    }
  }, [handleZoomInputSubmit]);


  return (
    <Paper elevation={2} sx={{ m: 2, p: 2, pb: 0 }}>
      <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
        <Box flex={1}>
          <Typography variant="h4" gutterBottom>
            {language === 'en' ? 'Slovenia Government Timeline (1990-2026)' : 'Časovnica slovenskih vlad (1990-2026)'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {language === 'en'
              ? 'Horizontal timeline showing ministers and prime ministers across different governments. Colors represent governments. Sort by first appearance or frequency. Hover to see total government roles for each person (including PM positions). Click on governments to filter ministries.'
              : 'Horizontalna časovnica, ki prikazuje ministre in predsednike vlad v različnih vladah. Barve predstavljajo vlade. Razvrsti po prvi pojavitvi ali pogostosti. Premaknite miško za ogled skupnega števila vladinih vlog za vsako osebo (vključno s predsedništvom vlad). Kliknite na vlade za filtriranje ministrstev.'
            }
          </Typography>
          {selectedGovernment && (
            <Box sx={{ mt: 1 }}>
              <Chip
                label={language === 'en'
                  ? `Filtered: Government ${selectedGovernment} ministries at top`
                  : `Filtrirano: Ministrstva vlade ${selectedGovernment} na vrhu`
                }
                color="primary"
                size="small"
                onDelete={() => setSelectedGovernment(null)}
                sx={{ mr: 1 }}
              />
              <Typography variant="caption" color="text.secondary">
                {language === 'en'
                  ? 'Click the government again or use the × to clear filter'
                  : 'Ponovno kliknite na vlado ali uporabite × za odstranitev filtra'
                }
              </Typography>
            </Box>
          )}
        </Box>

        <Box display="flex" alignItems="center" gap={2}>
          <Box display="flex" flexDirection="column" alignItems="center" gap={1}>
            <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
              {language === 'en' ? 'Sort' : 'Razvrsti'}
            </Typography>
            <ToggleButtonGroup
              value={sortMode}
              exclusive
              onChange={(_, newSortMode) => {
                if (newSortMode) setSortMode(newSortMode);
              }}
              size="small"
              sx={{ height: '28px' }}
            >
              <Tooltip
                title={language === 'en'
                  ? 'Sort by when each ministry first appeared'
                  : 'Razvrsti po tem, kdaj se je vsako ministrstvo prvič pojavilo'
                }
                arrow
              >
                <ToggleButton value="first-appearance" sx={{ px: 1, fontSize: '0.6rem' }}>
                  {language === 'en' ? 'First' : 'Prvi'}
                </ToggleButton>
              </Tooltip>
              <Tooltip
                title={language === 'en'
                  ? 'Sort by how many times each ministry was filled'
                  : 'Razvrsti po tem, kolikokrat je bilo vsako ministrstvo zasedeno'
                }
                arrow
              >
                <ToggleButton value="frequency" sx={{ px: 1, fontSize: '0.6rem' }}>
                  {language === 'en' ? 'Freq' : 'Pog'}
                </ToggleButton>
              </Tooltip>
            </ToggleButtonGroup>
          </Box>

          <Box display="flex" flexDirection="column" alignItems="center" gap={1}>
            <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
              {language === 'en' ? 'Language' : 'Jezik'}
            </Typography>
            <ToggleButtonGroup
              value={language}
              exclusive
              onChange={(_, newLanguage) => {
                if (newLanguage) setLanguage(newLanguage);
              }}
              size="small"
              sx={{ height: '28px' }}
            >
              <ToggleButton value="en" sx={{ px: 1, fontSize: '0.75rem' }}>
                EN
              </ToggleButton>
              <ToggleButton value="sl" sx={{ px: 1, fontSize: '0.75rem' }}>
                SL
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>

          <Box display="flex" flexDirection="column" alignItems="center" gap={1}>
            <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
              {language === 'en' ? 'Zoom' : 'Povečava'}
            </Typography>
            <Box display="flex" alignItems="center" gap={1}>
          <Chip
            label="-"
            size="small"
            onClick={() => handleZoom(-0.2)}
            sx={{ minWidth: '32px', cursor: 'pointer' }}
          />
          <TextField
            value={zoomInput}
            onChange={handleZoomInputChange}
            onBlur={handleZoomInputSubmit}
            onKeyPress={handleZoomInputKeyPress}
            size="small"
            sx={{
              width: '60px',
              '& .MuiInputBase-input': {
                textAlign: 'center',
                fontSize: '0.875rem',
                padding: '4px 8px',
              }
            }}
            InputProps={{
              endAdornment: <Typography variant="caption" sx={{ color: 'text.secondary', ml: 0.5 }}>%</Typography>
            }}
          />
          <Chip
            label="+"
            size="small"
            onClick={() => handleZoom(0.2)}
            sx={{ minWidth: '32px', cursor: 'pointer' }}
          />
          <Chip
            label="Fit"
            size="small"
            onClick={() => {
              const fitZoom = calculateFitToScreenZoom();
              setZoomLevel(fitZoom);
              setZoomInput((fitZoom * 100).toFixed(1));
            }}
            sx={{ cursor: 'pointer' }}
          />
            </Box>
          </Box>
        </Box>
      </Box>

      <TimelineContainer
        ref={scrollRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        <TimelineContent>
          {/* Date hover indicator */}
          {mouseDate && mousePosition && (
            <DateHoverIndicator
              style={{
                left: mousePosition.x,
                top: mousePosition.y,
              }}
            >
              {mouseDate}
            </DateHoverIndicator>
          )}

          {/* Mobile click date indicator */}
          {clickedBarDate && (
            <DateHoverIndicator
              style={{
                left: clickedBarDate.position.x,
                top: clickedBarDate.position.y,
              }}
            >
              {clickedBarDate.date}
            </DateHoverIndicator>
          )}

          {/* Year timeline indicators at the top */}
          <YearTimelineRow>
            <MinistryLabel>
              <Typography
                variant="body2"
                sx={{
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  width: '100%',
                  color: 'text.secondary',
                  [`@media (max-width:768px)`]: {
                    fontSize: '0.6rem',
                  }
                }}
              >
                {language === 'en' ? 'Timeline' : 'Časovnica'}
              </Typography>
            </MinistryLabel>
            <YearTimeline timelineWidth={totalTimelineWidth}>
              {yearMarkers.map(({ year, position }) => (
                <YearIndicator key={`year-${year}`} style={{ left: `${position}px` }}>
                  {year}
                </YearIndicator>
              ))}
            </YearTimeline>
          </YearTimelineRow>

          {/* Government row as second row */}
          <GovernmentRow>
            <MinistryLabel>
              <Typography
                variant="body2"
                sx={{
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  width: '100%',
                  [`@media (max-width:768px)`]: {
                    fontSize: '0.65rem',
                  }
                }}
              >
                {language === 'en' ? 'Governments' : 'Vlade'}
              </Typography>
            </MinistryLabel>
            <MinistryTimeline timelineWidth={totalTimelineWidth}>
              {/* Government bars */}
              {governmentData.map((government) => {
                const startPos = getPositionFromDate(government.startDate);
                const width = getWidthFromDates(government.startDate, government.endDate);

                return (
                  <Tooltip
                    key={government.number}
                    title={
                      <Box>
                        <Typography variant="subtitle2">
                          {language === 'en' ? `Government ${government.number}` : `Vlada ${government.number}`}
                        </Typography>
                        <Typography variant="body2">{government.name}</Typography>
                        <Typography variant="caption">
                          {language === 'en' ? 'Prime Minister:' : 'Predsednik vlade:'} {government.primeMinister}
                        </Typography>
                        <Typography variant="caption" display="block">
                          {government.startDate} {language === 'en' ? 'to' : 'do'} {government.endDate}
                        </Typography>
                        {(() => {
                          const govData = (ministersData.governments as Government[]).find(g => g.number === government.number);
                          if (govData?.political_composition) {
                            return (
                              <>
                                <Typography variant="caption" display="block" sx={{ mt: 0.5, fontWeight: 600 }}>
                                  {language === 'en' ? 'Coalition:' : 'Koalicija:'} {language === 'en' ? govData.political_composition.coalition.en : govData.political_composition.coalition.sl}
                                </Typography>
                                <Typography variant="caption" display="block">
                                  {language === 'en' ? 'Parties:' : 'Stranke:'} {govData.political_composition.parties.join(', ')}
                                </Typography>
                              </>
                            );
                          }
                          return null;
                        })()}
                      </Box>
                    }
                    arrow
                    placement="top"
                    leaveDelay={0}
                    enterDelay={100}
                    disableInteractive={true}
                  >
                    <GovernmentBar
                      isSelected={selectedGovernment === government.number}
                      style={{
                        left: `${startPos}px`,
                        width: `${width}px`,
                        backgroundColor: government.color,
                        paddingLeft: '8px',
                        paddingRight: '4px',
                      }}
                      onClick={(e) => {
                        if (isMobileDevice()) {
                          handleBarClick(e, government.startDate, government.endDate);
                        } else {
                          e.stopPropagation();
                          handleGovernmentClick(government.number);
                        }
                      }}
                    >
                      <Box sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 0.5,
                        width: '100%',
                        overflow: 'hidden'
                      }}>
                        <Typography
                          variant="caption"
                          sx={{
                            fontSize: '0.7rem',
                            fontWeight: 600,
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            flexGrow: 1,
                            minWidth: 0
                          }}
                        >
                          Gov {government.number}: {government.primeMinister}
                        </Typography>
                      </Box>
                    </GovernmentBar>
                  </Tooltip>
                );
              })}
            </MinistryTimeline>
          </GovernmentRow>

          {/* Prime Minister row as third row */}
          <PrimeMinisterRow>
            <MinistryLabel>
              <Typography
                variant="body2"
                sx={{
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  width: '100%',
                  [`@media (max-width:768px)`]: {
                    fontSize: '0.65rem',
                  }
                }}
              >
                {language === 'en' ? 'Prime Ministers' : 'Predsedniki vlad'}
              </Typography>
            </MinistryLabel>
            <MinistryTimeline timelineWidth={totalTimelineWidth}>
              {/* Prime Minister bars */}
              {governmentData.map((government) => {
                const startPos = getPositionFromDate(government.startDate);
                const width = getWidthFromDates(government.startDate, government.endDate);

                return (
                  <Tooltip
                    key={`pm-${government.number}`}
                    title={
                      <Box>
                        <Typography variant="subtitle2">{government.primeMinister}</Typography>
                        <Typography variant="body2">
                          {language === 'en' ? 'Prime Minister' : 'Predsednik vlade'}
                        </Typography>
                        <Typography variant="caption">
                          {government.startDate} {language === 'en' ? 'to' : 'do'} {government.endDate}
                        </Typography>
                        <Typography variant="caption" display="block">
                          {language === 'en' ? 'Government' : 'Vlada'} {government.number}: {government.name}
                        </Typography>
                        <Typography variant="caption" display="block" sx={{ fontWeight: 600, mt: 0.5 }}>
                          {language === 'en'
                            ? `Total gov roles: ${government.primeMinisterRoleCount}`
                            : `Skupaj vl. vlog: ${government.primeMinisterRoleCount}`}
                        </Typography>
                      </Box>
                    }
                    arrow
                    placement="top"
                    leaveDelay={0}
                    enterDelay={100}
                    disableInteractive={true}
                  >
                    <MinisterBar
                      isPersonHighlighted={hoveredPerson === government.primeMinister}
                      style={{
                        left: `${startPos}px`,
                        width: `${width}px`,
                        backgroundColor: government.color,
                        paddingLeft: '8px',
                        paddingRight: '4px',
                      }}
                      onMouseEnter={() => setHoveredPerson(government.primeMinister)}
                      onMouseLeave={() => setHoveredPerson(null)}
                      onClick={(e) => {
                        if (isMobileDevice()) {
                          handleBarClick(e, government.startDate, government.endDate);
                        }
                      }}
                    >
                      <Box sx={{
                        display: 'flex',
                        alignItems: 'center',
                        width: '100%',
                        overflow: 'hidden'
                      }}>
                        <Typography
                          variant="caption"
                          sx={{
                            fontSize: '0.7rem',
                            fontWeight: 500,
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            width: '100%'
                          }}
                        >
                          {government.primeMinister}
                        </Typography>
                      </Box>
                    </MinisterBar>
                  </Tooltip>
                );
              })}
            </MinistryTimeline>
          </PrimeMinisterRow>

          {/* Ministry rows */}
          {processedData.map((ministry) => (
            <MinistryRow key={ministry.name}>
              <MinistryLabel isHovered={hoveredMinistry === ministry.name}>
                <Typography
                  variant="body2"
                  sx={{
                    fontSize: '0.75rem',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    width: '100%',
                    [`@media (max-width:768px)`]: {
                      fontSize: '0.65rem',
                    }
                  }}
                >
                  {ministry.name}
                </Typography>
              </MinistryLabel>
              <MinistryTimeline
                timelineWidth={totalTimelineWidth}
                onMouseEnter={() => setHoveredMinistry(ministry.name)}
                onMouseLeave={() => setHoveredMinistry(null)}
              >
                {ministry.ministers.map((minister, index) => {
                  const startPos = getPositionFromDate(minister.start_date);
                  const width = getWidthFromDates(minister.start_date, minister.end_date);

                  return (
                    <Tooltip
                      key={`${minister.name}-${index}`}
                      title={
                        <Box>
                          <Typography variant="subtitle2">{minister.name}</Typography>
                          <Typography variant="body2">
                            {language === 'en' ? minister.title.en : minister.title.sl}
                          </Typography>
                          <Typography variant="caption">
                            {minister.start_date} {language === 'en' ? 'to' : 'do'} {minister.end_date}
                          </Typography>
                          <Typography variant="caption" display="block">
                            {language === 'en' ? 'Government' : 'Vlada'} {minister.governmentNumber}: {minister.governmentName}
                          </Typography>
                          <Typography variant="caption" display="block">
                            {language === 'en' ? 'PM:' : 'PV:'} {minister.primeMinister}
                          </Typography>
                          <Typography variant="caption" display="block" sx={{ fontWeight: 600, mt: 0.5 }}>
                            {language === 'en'
                              ? `Total gov roles: ${minister.roleCount}`
                              : `Skupaj vl. vlog: ${minister.roleCount}`}
                          </Typography>
                        </Box>
                      }
                      arrow
                      placement="top"
                      leaveDelay={0}
                      enterDelay={100}
                      disableInteractive={true}
                    >
                      <MinisterBar
                        isPersonHighlighted={hoveredPerson === minister.name}
                        style={{
                          left: `${startPos}px`,
                          width: `${width}px`,
                          backgroundColor: minister.governmentColor,
                          paddingLeft: '8px',
                          paddingRight: '4px',
                        }}
                        onMouseEnter={() => setHoveredPerson(minister.name)}
                        onMouseLeave={() => setHoveredPerson(null)}
                        onClick={(e) => {
                          if (isMobileDevice()) {
                            handleBarClick(e, minister.start_date, minister.end_date);
                          }
                        }}
                      >
                        <Box sx={{
                          display: 'flex',
                          alignItems: 'center',
                          width: '100%',
                          overflow: 'hidden'
                        }}>
                          <Typography
                            variant="caption"
                            sx={{
                              fontSize: '0.7rem',
                              fontWeight: 500,
                              whiteSpace: 'nowrap',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              width: '100%'
                            }}
                          >
                            {minister.name}
                          </Typography>
                        </Box>
                      </MinisterBar>
                    </Tooltip>
                  );
                })}
              </MinistryTimeline>
            </MinistryRow>
          ))}
        </TimelineContent>
      </TimelineContainer>
    </Paper>
  );
}