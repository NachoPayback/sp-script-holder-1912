import React from 'react';
import styled from 'styled-components';
import { HexagonButton } from './HexagonButton';
import type { HubScript, Assignment } from '../../types/Hub';
import { generateScriptColor } from '../../utils/colors';
import { theme } from '../../styles/theme';

interface ScriptGridProps {
  scripts: HubScript[];
  assignment?: Assignment;
  mode: 'shared' | 'assigned';
  showScriptNames: boolean;
  friendlyNames: Record<string, { friendly_name: string; image_url?: string; custom_color?: string; position_x?: number; position_y?: number; image_scale?: number }>;
  onScriptExecute: (scriptName: string) => void;
  isEditMode?: boolean;
}

const GridContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: ${theme.spacing.xl};  /* Reduced from xxl */
  padding: ${theme.spacing.xl};  /* Reduced from xxl */
  justify-items: center;
  max-width: 1200px;  /* Reduced from 1400px */
  margin: 0 auto;
  position: relative;
  
  /* Modern floating grid effect */
  &::before {
    content: '';
    position: absolute;
    top: -20px;
    left: -20px;
    right: -20px;
    bottom: -20px;
    background: 
      linear-gradient(135deg, rgba(10, 10, 10, 0.8) 0%, rgba(20, 20, 20, 0.6) 100%);
    border-radius: ${theme.borderRadius.xxl};
    backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid ${theme.colors.borderLight};
    box-shadow: 
      0 20px 40px rgba(0, 0, 0, 0.4),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
    z-index: -1;
  }
`;

const LoadingMessage = styled.div`
  color: ${theme.colors.textSecondary};
  text-align: center;
  font-family: ${theme.fonts.family};
  font-size: 1.1rem;
  padding: ${theme.spacing.xxl};
`;

export const ScriptGrid: React.FC<ScriptGridProps> = ({
  scripts,
  assignment,
  mode,
  showScriptNames,
  friendlyNames,
  onScriptExecute,
  isEditMode = false
}) => {
  if (mode === 'assigned') {
    if (!assignment?.assigned_script) {
      return <LoadingMessage>Waiting for assignment...</LoadingMessage>;
    }

    return (
      <GridContainer>
        <HexagonButton
          scriptName={assignment.assigned_script}
          color={assignment.script_color || theme.colors.primary}
          friendlyName={friendlyNames[assignment.assigned_script]?.friendly_name}
          imageUrl={friendlyNames[assignment.assigned_script]?.image_url}
          imagePositionX={friendlyNames[assignment.assigned_script]?.position_x || 0}
          imagePositionY={friendlyNames[assignment.assigned_script]?.position_y || 0}
          imageScale={friendlyNames[assignment.assigned_script]?.image_scale || 100}
          showName={showScriptNames}
          onClick={() => onScriptExecute(assignment.assigned_script)}
          isEditMode={isEditMode}
        />
      </GridContainer>
    );
  }

  if (scripts.length === 0) {
    return <LoadingMessage>No scripts available</LoadingMessage>;
  }

  return (
    <GridContainer>
      {scripts.map((script, index) => {
        const scriptName = typeof script === 'string' ? script : script.script_name;
        // Use custom color if available, otherwise generate automatic color
        const color = friendlyNames[scriptName]?.custom_color || generateScriptColor(index);
        // Prioritize friendly names from database over script object
        const friendlyName = friendlyNames[scriptName]?.friendly_name;
        const imageUrl = friendlyNames[scriptName]?.image_url;
        const imagePositionX = friendlyNames[scriptName]?.position_x || 0;
        const imagePositionY = friendlyNames[scriptName]?.position_y || 0;
        const imageScale = friendlyNames[scriptName]?.image_scale || 100;
        
        return (
          <HexagonButton
            key={scriptName}
            scriptName={scriptName}
            color={color}
            friendlyName={friendlyName}
            imageUrl={imageUrl}
            imagePositionX={imagePositionX}
            imagePositionY={imagePositionY}
            imageScale={imageScale}
            showName={true} // Always show names in shared mode
            onClick={() => onScriptExecute(scriptName)}
            isEditMode={isEditMode}
          />
        );
      })}
      
    </GridContainer>
  );
};