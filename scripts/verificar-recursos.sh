#!/usr/bin/env bash
# verificar-recursos.sh — inventário de EC2 e RDS ligados na sua conta AWS.
#
# Não apaga nada e não desliga nada por conta própria: só lista o que está
# de pé, região por região, e imprime o comando exato para você mesmo
# desligar cada recurso encontrado.
#
# Usa as credenciais já autenticadas no seu ambiente (aws configure, ou
# automaticamente se estiver no AWS CloudShell) — nunca uma access key
# gravada em arquivo.
#
# Uso:
#   ./verificar-recursos.sh                       # região padrão configurada
#   ./verificar-recursos.sh us-east-1              # uma região
#   ./verificar-recursos.sh us-east-1 sa-east-1    # várias regiões

set -uo pipefail

REGIOES=("$@")

if [[ ${#REGIOES[@]} -eq 0 ]]; then
  DEFAULT_REGION=$(aws configure get region 2>/dev/null)
  if [[ -z "$DEFAULT_REGION" ]]; then
    read -rp "Nenhuma região informada nem configurada. Digite a região (ex: us-east-1): " DEFAULT_REGION
  fi
  REGIOES=("$DEFAULT_REGION")
fi

for REGION in "${REGIOES[@]}"; do
  echo "======================================================"
  echo "Região: $REGION"
  echo "======================================================"

  echo
  echo "-- EC2 --"
  EC2_LINHAS=$(aws ec2 describe-instances --region "$REGION" \
    --query 'Reservations[].Instances[?State.Name!=`terminated`].[InstanceId,InstanceType,State.Name]' \
    --output text)

  if [[ -z "$EC2_LINHAS" ]]; then
    echo "(nenhuma instância)"
  else
    while read -r id tipo estado; do
      [[ -z "$id" ]] && continue
      echo "  $id  $tipo  $estado"
      if [[ "$estado" == "running" ]]; then
        echo "    -> ligada, custando agora. Para desligar:"
        echo "       aws ec2 stop-instances --region $REGION --instance-ids $id"
      fi
    done <<< "$EC2_LINHAS"
  fi

  echo
  echo "-- RDS --"
  RDS_LINHAS=$(aws rds describe-db-instances --region "$REGION" \
    --query 'DBInstances[].[DBInstanceIdentifier,DBInstanceClass,DBInstanceStatus]' \
    --output text)

  if [[ -z "$RDS_LINHAS" ]]; then
    echo "(nenhuma instância)"
  else
    while read -r id classe status; do
      [[ -z "$id" ]] && continue
      echo "  $id  $classe  $status"
      if [[ "$status" == "available" ]]; then
        echo "    -> ligado, custando agora. Para desligar:"
        echo "       aws rds stop-db-instance --region $REGION --db-instance-identifier $id"
        echo "       (atenção: um RDS parado volta a ligar por conta própria após 7 dias)"
      fi
    done <<< "$RDS_LINHAS"
  fi

  echo
  echo "-- VPC Endpoints de Interface -- (não têm 'stop': cobram por hora só de existir)"
  VPCE_LINHAS=$(aws ec2 describe-vpc-endpoints --region "$REGION" \
    --filters Name=vpc-endpoint-type,Values=Interface \
    --query 'VpcEndpoints[].[VpcEndpointId,ServiceName,State]' \
    --output text)

  if [[ -z "$VPCE_LINHAS" ]]; then
    echo "(nenhum)"
  else
    while read -r id servico estado; do
      [[ -z "$id" ]] && continue
      echo "  $id  $servico  $estado"
      echo "    -> cobrando enquanto existir. Para remover:"
      echo "       aws ec2 delete-vpc-endpoints --region $REGION --vpc-endpoint-ids $id"
    done <<< "$VPCE_LINHAS"
  fi

  echo
  echo "-- Elastic IPs -- (cobram sempre que não estão presos a uma instância rodando)"
  EIP_LINHAS=$(aws ec2 describe-addresses --region "$REGION" \
    --query 'Addresses[].[AllocationId,PublicIp,InstanceId]' \
    --output text)

  if [[ -z "$EIP_LINHAS" ]]; then
    echo "(nenhum)"
  else
    while read -r alloc ip instancia; do
      [[ -z "$alloc" ]] && continue
      [[ "$instancia" == "None" ]] && instancia=""
      echo "  $alloc  $ip  associado a: ${instancia:-nada}"
      if [[ -z "$instancia" ]]; then
        echo "    -> sem instância associada, cobrando agora. Para liberar:"
        echo "       aws ec2 release-address --region $REGION --allocation-id $alloc"
      fi
    done <<< "$EIP_LINHAS"
  fi
  echo
done
