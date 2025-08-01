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
  friendlyNames: Record<string, { friendly_name: string }>;
  onScriptExecute: (scriptName: string) => void;
}

const GridContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: ${theme.spacing.xl};
  padding: ${theme.spacing.lg};
  justify-items: center;
  max-width: 1200px;
  margin: 0 auto;
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
  onScriptExecute
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
          showName={showScriptNames}
          onClick={() => onScriptExecute(assignment.assigned_script)}
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
        const color = generateScriptColor(index);
        const scriptName = typeof script === 'string' ? script : script.script_name;
        const friendlyName = typeof script === 'string' ? script : script.friendly_name;
        
        return (
          <HexagonButton
            key={scriptName}
            scriptName={scriptName}
            color={color}
            friendlyName={friendlyName || friendlyNames[scriptName]?.friendly_name}
            showName={true} // Always show names in shared mode
            onClick={() => onScriptExecute(scriptName)}
          />
        );
      })}
    </GridContainer>
  );
};