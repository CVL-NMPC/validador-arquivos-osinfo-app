from datetime import datetime
from sqlalchemy import text
import json

class HistAlteracoesItemDespesas:
    def __init__(self, sqlConnSession = None, **kwargs):
        self.sqlConnSession = kwargs.get('sqlConnSession', sqlConnSession)
        self.id = kwargs.get('id', None)
        self.hist_alteracoes_despesas_id = kwargs.get('hist_alteracoes_despesas_id', None)
        self.id_despesa_osinfo = kwargs.get('id_despesa_osinfo', 'None')
        self.despesa_original = kwargs.get('despesa_original', '{"id_documento": 0}')
        self.despesa_alterada = kwargs.get('despesa_alterada', '{"id_documento": 0}')
        self.msg_osinfo = kwargs.get('msg_osinfo', None)
        self.revertido = kwargs.get('revertido', 0)
        self.msg_osinfo_reversao = kwargs.get('msg_osinfo_reversao', None)
        self.created_by = kwargs.get('created_by', 1)
        self.created_at = kwargs.get('created_at', datetime.now())

    def to_dict(self):
        return {
            "id": self.id,
            "hist_alteracoes_despesas_id": self.hist_alteracoes_despesas_id,
            "id_despesa_osinfo": self.id_despesa_osinfo,
            "despesa_original": self.despesa_original,
            "despesa_alterada": self.despesa_alterada,
            "msg_osinfo": self.msg_osinfo,
            "revertido": self.revertido,
            "msg_osinfo_reversao": self.msg_osinfo_reversao,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }

    @property
    def id_despesa_osinfo(self):
        return self._id_despesa_osinfo
    
    @id_despesa_osinfo.setter
    def id_despesa_osinfo(self, id_despesa_osinfo):
        self._id_despesa_osinfo = id_despesa_osinfo

    @property
    def despesa_original(self):
        return self._despesa_original

    @despesa_original.setter
    def despesa_original(self, despesa_original):
        if not isinstance(despesa_original, str):
            raise ValueError("despesa_original deve ser uma string formato json")
        try:
            parsed_json = json.loads(despesa_original)
            self._despesa_original = despesa_original
            self.id_despesa_osinfo = int(parsed_json['id_documento'])
        except json.JSONDecodeError:
            raise ValueError("A string não é um json válido")
        except KeyError:
            raise ValueError("O json nao possui a chave 'id_documento'")
        
    def __repr__(self):
        return f"<HistAlteracoesItemDespesas(id={self.id}, hist_alteracoes_despesas_id={self.hist_alteracoes_despesas_id})>"

    def load_from_id(self, id: int):
        with self.sqlConnSession as session:
            query = text("""SELECT * FROM hist_alteracoes_item_despesas WHERE id = :id""")
            result = session.execute(query, {"id" : id})
            row = result.fetchone()
            if row:
                self.id, self.hist_alteracoes_despesas_id, self.id_despesa_osinfo, self.despesa_original, \
                self.despesa_alterada, self.msg_osinfo, self.revertido, self.msg_osinfo_reversao, \
                self.created_by, self.created_at = row

    def store(self):
        with self.sqlConnSession as session:
            if self.id:
                query = text(""" UPDATE hist_alteracoes_item_despesas SET
                                    hist_alteracoes_despesas_id = :hist_alteracoes_despesas_id,
                                    id_despesa_osinfo = :id_despesa_osinfo,
                                    despesa_original = :despesa_original,
                                    despesa_alterada = :despesa_alterada,
                                    msg_osinfo = :msg_osinfo,
                                    revertido = :revertido,
                                    msg_osinfo_reversao = :msg_osinfo_reversao,
                                    created_by = :created_by,
                                    created_at = :created_at
                            WHERE id = :id """)
                result = session.execute(query, 
                            {
                            "hist_alteracoes_despesas_id": self.hist_alteracoes_despesas_id,
                            "id_despesa_osinfo": self.id_despesa_osinfo,
                            "despesa_original": self.despesa_original,
                            "despesa_alterada": self.despesa_alterada,
                            "msg_osinfo": self.msg_osinfo,
                            "revertido": self.revertido,
                            "msg_osinfo_reversao": self.msg_osinfo_reversao,
                            "created_by": self.created_by,
                            "created_at": self.created_at,
                            "id": self.id
                            }
                        )
            else:
                query = text("""
                        INSERT INTO hist_alteracoes_item_despesas (hist_alteracoes_despesas_id, id_despesa_osinfo, despesa_original, despesa_alterada, msg_osinfo, revertido, msg_osinfo_reversao, created_by, created_at)
                                            VALUES (:hist_alteracoes_despesas_id, :id_despesa_osinfo, :despesa_original, :despesa_alterada, :msg_osinfo, :revertido, :msg_osinfo_reversao, :created_by, :created_at)
                        """)
                result = session.execute(query, 
                            {
                            "hist_alteracoes_despesas_id": self.hist_alteracoes_despesas_id,
                            "id_despesa_osinfo": self.id_despesa_osinfo,
                            "despesa_original": self.despesa_original,
                            "despesa_alterada": self.despesa_alterada,
                            "msg_osinfo": self.msg_osinfo,
                            "revertido": self.revertido,
                            "msg_osinfo_reversao": self.msg_osinfo_reversao,
                            "created_by": self.created_by or 1,
                            "created_at": self.created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                        )
                #self.id = result.scalar()
            session.commit()
    def __repr__(self):
        return f"<HistAlteracoesItemDespesas(id={self.id}, hist_alteracoes_despesas_id={self.hist_alteracoes_despesas_id})>"


    @staticmethod
    def collection_load_by_criteria(connection, criteria: str, fields = 'hist.*') -> list:
        with connection as session:
            query = text(f"SELECT {fields} FROM hist_alteracoes_item_despesas hist WHERE {criteria}")
            result = session.execute(query) 
            results = result.mappings().fetchall()
        
        registros = []
        for row in results:
            result = HistAlteracoesItemDespesas(connection, **row)
            registros.append(result)
        return registros